"""
Cohort Builder for Retrospective Studies
Flexible querying system for building patient cohorts
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import date, datetime
from enum import Enum
import logging
from django.db.models import Q, F, Count, Avg, Min, Max, Sum, Subquery, OuterRef
from django.db.models.functions import ExtractYear
from django.db import connection

from oncology.models import (
    Patient, CancerType, CancerDiagnosis, Pathology, Cytogenetics,
    Treatment, TreatmentResponse, Relapse, Outcome, Biomarker,
    AdverseEvent, Comorbidity
)
from patient_portal.models import PatientConsent, DataAccessGrant

logger = logging.getLogger(__name__)


class Operator(Enum):
    """Query operators for cohort criteria"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    BETWEEN = "between"
    IS_NULL = "isnull"
    EXISTS = "exists"


class LogicalOperator(Enum):
    """Logical operators for combining criteria"""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class Criterion:
    """
    Single criterion for cohort selection
    """
    field: str  # e.g., "age_at_diagnosis", "cancer_type", "treatment.regimen_name"
    operator: Operator
    value: Any  # Can be single value, list, or tuple for BETWEEN
    
    def to_q(self) -> Q:
        """Convert criterion to Django Q object"""
        django_field = self._map_field_to_django(self.field)
        
        if self.operator == Operator.EQUALS:
            return Q(**{django_field: self.value})
        elif self.operator == Operator.NOT_EQUALS:
            return ~Q(**{django_field: self.value})
        elif self.operator == Operator.GREATER_THAN:
            return Q(**{f"{django_field}__gt": self.value})
        elif self.operator == Operator.GREATER_THAN_OR_EQUAL:
            return Q(**{f"{django_field}__gte": self.value})
        elif self.operator == Operator.LESS_THAN:
            return Q(**{f"{django_field}__lt": self.value})
        elif self.operator == Operator.LESS_THAN_OR_EQUAL:
            return Q(**{f"{django_field}__lte": self.value})
        elif self.operator == Operator.IN:
            return Q(**{f"{django_field}__in": self.value})
        elif self.operator == Operator.NOT_IN:
            return ~Q(**{f"{django_field}__in": self.value})
        elif self.operator == Operator.CONTAINS:
            return Q(**{f"{django_field}__contains": self.value})
        elif self.operator == Operator.ICONTAINS:
            return Q(**{f"{django_field}__icontains": self.value})
        elif self.operator == Operator.BETWEEN:
            return Q(**{f"{django_field}__gte": self.value[0], f"{django_field}__lte": self.value[1]})
        elif self.operator == Operator.IS_NULL:
            return Q(**{f"{django_field}__isnull": self.value})
        elif self.operator == Operator.EXISTS:
            # For related objects
            return Q(**{f"{django_field}__isnull": not self.value})
        
        raise ValueError(f"Unknown operator: {self.operator}")
    
    def _map_field_to_django(self, field: str) -> str:
        """Map user-friendly field names to Django field paths"""
        field_mapping = {
            # Patient fields
            "age": "birth_year",  # Will need special handling
            "sex": "sex",
            "race": "race",
            "ethnicity": "ethnicity",
            
            # Diagnosis fields
            "cancer_type": "diagnoses__cancer_type__name",
            "cancer_category": "diagnoses__cancer_type__category",
            "icd_code": "diagnoses__cancer_type__icd_o3_code",
            "diagnosis_date": "diagnoses__diagnosis_date",
            "age_at_diagnosis": "diagnoses__age_at_diagnosis",
            "clinical_stage": "diagnoses__clinical_stage",
            "pathologic_stage": "diagnoses__pathologic_stage",
            "t_stage": "diagnoses__t_stage",
            "n_stage": "diagnoses__n_stage",
            "m_stage": "diagnoses__m_stage",
            "risk_group": "diagnoses__risk_group",
            "ecog_ps": "diagnoses__ecog_ps",
            
            # Pathology fields
            "histology": "diagnoses__pathology_reports__histology",
            "grade": "diagnoses__pathology_reports__histologic_grade",
            
            # Cytogenetics/Molecular fields
            "mutation": "diagnoses__cytogenetics__mutations_detected",
            "molecular_marker": "diagnoses__cytogenetics__molecular_markers",
            "molecular_risk": "diagnoses__cytogenetics__molecular_risk_group",
            "karyotype": "diagnoses__cytogenetics__karyotype",
            
            # Treatment fields
            "treatment_type": "diagnoses__treatments__treatment_type",
            "treatment_intent": "diagnoses__treatments__treatment_intent",
            "regimen": "diagnoses__treatments__regimen_name",
            "treatment_line": "diagnoses__treatments__treatment_line",
            "treatment_start": "diagnoses__treatments__start_date",
            "transplant_type": "diagnoses__treatments__transplant_type",
            
            # Response fields
            "response": "diagnoses__treatments__responses__response_type",
            "best_response": "diagnoses__treatments__responses__best_response",
            "mrd_status": "diagnoses__treatments__responses__mrd_result",
            
            # Relapse fields
            "relapse_count": "diagnoses__relapses__relapse_number",
            "is_refractory": "diagnoses__relapses__is_refractory",
            "is_transformed": "diagnoses__relapses__is_transformed",
            
            # Outcome fields
            "vital_status": "outcomes__vital_status",
            "disease_status": "outcomes__disease_status",
            "overall_survival": "outcomes__overall_survival_months",
            "progression_free_survival": "outcomes__progression_free_survival_months",
            
            # Biomarker fields
            "biomarker_name": "biomarkers__biomarker_name",
            "biomarker_value": "biomarkers__value",
            
            # Adverse event fields
            "adverse_event": "diagnoses__treatments__adverse_events__event_term",
            "ae_grade": "diagnoses__treatments__adverse_events__ctcae_grade",
            
            # Comorbidity fields
            "comorbidity": "comorbidities__condition_name",
            "comorbidity_icd": "comorbidities__icd10_code",
        }
        
        return field_mapping.get(field, field)


@dataclass
class CriteriaGroup:
    """
    Group of criteria combined with logical operator
    """
    operator: LogicalOperator
    criteria: List[Union[Criterion, 'CriteriaGroup']]
    
    def to_q(self) -> Q:
        """Convert criteria group to Django Q object"""
        if not self.criteria:
            return Q()
        
        q_objects = [c.to_q() for c in self.criteria]
        
        if self.operator == LogicalOperator.AND:
            result = q_objects[0]
            for q in q_objects[1:]:
                result &= q
            return result
        elif self.operator == LogicalOperator.OR:
            result = q_objects[0]
            for q in q_objects[1:]:
                result |= q
            return result
        elif self.operator == LogicalOperator.NOT:
            if len(q_objects) != 1:
                raise ValueError("NOT operator requires exactly one criterion")
            return ~q_objects[0]
        
        raise ValueError(f"Unknown logical operator: {self.operator}")


@dataclass
class CohortDefinition:
    """
    Complete cohort definition with all criteria
    """
    name: str
    description: str
    inclusion_criteria: CriteriaGroup
    exclusion_criteria: Optional[CriteriaGroup] = None
    
    # Data access constraints
    require_consent: bool = True
    require_irb_approval: bool = True
    access_request_id: Optional[str] = None
    
    # Output configuration
    output_fields: List[str] = field(default_factory=list)
    include_longitudinal: bool = True
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class CohortBuilder:
    """
    Main class for building and executing cohort queries
    """
    
    def __init__(self, cohort_definition: CohortDefinition):
        self.definition = cohort_definition
        self._base_queryset = None
    
    def build_queryset(self) -> 'QuerySet':
        """
        Build Django queryset from cohort definition
        """
        # Start with patients who have given consent (if required)
        if self.definition.require_consent:
            queryset = Patient.objects.filter(
                data_sharing_level__in=['research_only', 'full']
            )
        else:
            queryset = Patient.objects.all()
        
        # Apply inclusion criteria
        inclusion_q = self.definition.inclusion_criteria.to_q()
        queryset = queryset.filter(inclusion_q)
        
        # Apply exclusion criteria
        if self.definition.exclusion_criteria:
            exclusion_q = self.definition.exclusion_criteria.to_q()
            queryset = queryset.exclude(exclusion_q)
        
        # Make distinct to avoid duplicates from joins
        queryset = queryset.distinct()
        
        self._base_queryset = queryset
        return queryset
    
    def count(self) -> int:
        """Get count of patients in cohort"""
        if self._base_queryset is None:
            self.build_queryset()
        return self._base_queryset.count()
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for the cohort
        """
        if self._base_queryset is None:
            self.build_queryset()
        
        patients = self._base_queryset
        current_year = datetime.now().year
        
        # Basic demographics
        demographics = patients.aggregate(
            total_patients=Count('id'),
            male_count=Count('id', filter=Q(sex='male')),
            female_count=Count('id', filter=Q(sex='female')),
            avg_age=Avg(current_year - F('birth_year')),
            min_age=Min(current_year - F('birth_year')),
            max_age=Max(current_year - F('birth_year')),
        )
        
        # Cancer type distribution
        diagnoses = CancerDiagnosis.objects.filter(
            patient__in=patients
        )
        
        cancer_types = diagnoses.values(
            'cancer_type__name', 'cancer_type__category'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Stage distribution
        stage_dist = diagnoses.values('clinical_stage').annotate(
            count=Count('id')
        ).order_by('clinical_stage')
        
        # Treatment distribution
        treatments = Treatment.objects.filter(
            diagnosis__patient__in=patients
        )
        
        treatment_types = treatments.values('treatment_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Outcome summary
        outcomes = Outcome.objects.filter(
            patient__in=patients
        )
        
        outcome_summary = outcomes.aggregate(
            alive_count=Count('id', filter=Q(vital_status='alive')),
            deceased_count=Count('id', filter=Q(vital_status='deceased')),
            avg_os=Avg('overall_survival_months'),
            avg_pfs=Avg('progression_free_survival_months'),
        )
        
        return {
            'demographics': demographics,
            'cancer_types': list(cancer_types),
            'stage_distribution': list(stage_dist),
            'treatment_types': list(treatment_types),
            'outcomes': outcome_summary,
        }
    
    def get_longitudinal_data(self) -> Dict[str, Any]:
        """
        Get longitudinal data for cohort analysis
        Returns timeline of events for each patient
        """
        if self._base_queryset is None:
            self.build_queryset()
        
        patients = self._base_queryset
        
        longitudinal_data = []
        
        for patient in patients[:100]:  # Limit for performance
            timeline = []
            
            # Diagnoses
            for dx in patient.diagnoses.all():
                timeline.append({
                    'date': dx.diagnosis_date,
                    'event_type': 'diagnosis',
                    'details': {
                        'cancer_type': dx.cancer_type.name,
                        'stage': dx.clinical_stage,
                    }
                })
                
                # Treatments
                for tx in dx.treatments.all():
                    timeline.append({
                        'date': tx.start_date,
                        'event_type': 'treatment_start',
                        'details': {
                            'type': tx.treatment_type,
                            'regimen': tx.regimen_name,
                            'line': tx.treatment_line,
                        }
                    })
                    
                    if tx.end_date:
                        timeline.append({
                            'date': tx.end_date,
                            'event_type': 'treatment_end',
                            'details': {
                                'type': tx.treatment_type,
                                'regimen': tx.regimen_name,
                            }
                        })
                    
                    # Responses
                    for resp in tx.responses.all():
                        timeline.append({
                            'date': resp.assessment_date,
                            'event_type': 'response',
                            'details': {
                                'response': resp.response_type,
                                'best_response': resp.best_response,
                            }
                        })
                
                # Relapses
                for relapse in dx.relapses.all():
                    timeline.append({
                        'date': relapse.relapse_date,
                        'event_type': 'relapse',
                        'details': {
                            'number': relapse.relapse_number,
                            'sites': relapse.relapse_site,
                        }
                    })
            
            # Outcomes
            for outcome in patient.outcomes.all():
                timeline.append({
                    'date': outcome.last_followup_date,
                    'event_type': 'outcome',
                    'details': {
                        'vital_status': outcome.vital_status,
                        'disease_status': outcome.disease_status,
                    }
                })
            
            # Sort timeline by date
            timeline.sort(key=lambda x: x['date'] if x['date'] else date.min)
            
            longitudinal_data.append({
                'patient_id': str(patient.id),
                'timeline': timeline,
            })
        
        return {
            'patients': longitudinal_data,
            'total_count': patients.count(),
        }
    
    def export_cohort(
        self,
        format: str = 'csv',
        fields: List[str] = None
    ) -> Union[str, bytes]:
        """
        Export cohort data in specified format
        """
        if self._base_queryset is None:
            self.build_queryset()
        
        fields = fields or self.definition.output_fields or self._get_default_fields()
        
        # Build export data
        export_data = self._build_export_data(fields)
        
        if format == 'csv':
            return self._export_csv(export_data, fields)
        elif format == 'json':
            return self._export_json(export_data)
        elif format == 'parquet':
            return self._export_parquet(export_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _get_default_fields(self) -> List[str]:
        """Get default export fields"""
        return [
            'patient_id', 'sex', 'age_at_diagnosis',
            'cancer_type', 'stage', 'diagnosis_date',
            'first_line_treatment', 'best_response',
            'vital_status', 'overall_survival_months'
        ]
    
    def _build_export_data(self, fields: List[str]) -> List[Dict[str, Any]]:
        """Build export data for cohort"""
        data = []
        
        for patient in self._base_queryset:
            row = {'patient_id': str(patient.id)}
            
            # Patient-level fields
            if 'sex' in fields:
                row['sex'] = patient.sex
            if 'race' in fields:
                row['race'] = patient.race
            if 'ethnicity' in fields:
                row['ethnicity'] = patient.ethnicity
            
            # Get first diagnosis
            first_dx = patient.diagnoses.order_by('diagnosis_date').first()
            if first_dx:
                if 'cancer_type' in fields:
                    row['cancer_type'] = first_dx.cancer_type.name
                if 'stage' in fields:
                    row['stage'] = first_dx.clinical_stage
                if 'diagnosis_date' in fields:
                    row['diagnosis_date'] = str(first_dx.diagnosis_date)
                if 'age_at_diagnosis' in fields:
                    row['age_at_diagnosis'] = first_dx.age_at_diagnosis
                
                # First line treatment
                first_tx = first_dx.treatments.filter(treatment_line=1).first()
                if first_tx and 'first_line_treatment' in fields:
                    row['first_line_treatment'] = first_tx.regimen_name
                
                # Best response
                if 'best_response' in fields:
                    best_resp = TreatmentResponse.objects.filter(
                        treatment__diagnosis=first_dx,
                        best_response=True
                    ).first()
                    row['best_response'] = best_resp.response_type if best_resp else None
            
            # Latest outcome
            latest_outcome = patient.outcomes.order_by('-last_followup_date').first()
            if latest_outcome:
                if 'vital_status' in fields:
                    row['vital_status'] = latest_outcome.vital_status
                if 'overall_survival_months' in fields:
                    row['overall_survival_months'] = latest_outcome.overall_survival_months
                if 'progression_free_survival_months' in fields:
                    row['progression_free_survival_months'] = latest_outcome.progression_free_survival_months
            
            data.append(row)
        
        return data
    
    def _export_csv(self, data: List[Dict], fields: List[str]) -> str:
        """Export to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    
    def _export_json(self, data: List[Dict]) -> str:
        """Export to JSON format"""
        import json
        return json.dumps(data, indent=2, default=str)
    
    def _export_parquet(self, data: List[Dict]) -> bytes:
        """Export to Parquet format"""
        import pandas as pd
        import io
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()


class CohortQueryDSL:
    """
    Domain-specific language for cohort queries
    Provides a fluent interface for building cohorts
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._inclusions: List[Criterion] = []
        self._exclusions: List[Criterion] = []
        self._output_fields: List[str] = []
    
    def include(
        self,
        field: str,
        operator: str,
        value: Any
    ) -> 'CohortQueryDSL':
        """Add inclusion criterion"""
        op = Operator(operator)
        self._inclusions.append(Criterion(field, op, value))
        return self
    
    def exclude(
        self,
        field: str,
        operator: str,
        value: Any
    ) -> 'CohortQueryDSL':
        """Add exclusion criterion"""
        op = Operator(operator)
        self._exclusions.append(Criterion(field, op, value))
        return self
    
    def age_range(self, min_age: int = None, max_age: int = None) -> 'CohortQueryDSL':
        """Filter by age range at diagnosis"""
        if min_age:
            self._inclusions.append(Criterion('age_at_diagnosis', Operator.GREATER_THAN_OR_EQUAL, min_age))
        if max_age:
            self._inclusions.append(Criterion('age_at_diagnosis', Operator.LESS_THAN_OR_EQUAL, max_age))
        return self
    
    def cancer_type(self, *types: str) -> 'CohortQueryDSL':
        """Filter by cancer type(s)"""
        if len(types) == 1:
            self._inclusions.append(Criterion('cancer_type', Operator.EQUALS, types[0]))
        else:
            self._inclusions.append(Criterion('cancer_type', Operator.IN, list(types)))
        return self
    
    def stage(self, *stages: str) -> 'CohortQueryDSL':
        """Filter by clinical stage(s)"""
        if len(stages) == 1:
            self._inclusions.append(Criterion('clinical_stage', Operator.EQUALS, stages[0]))
        else:
            self._inclusions.append(Criterion('clinical_stage', Operator.IN, list(stages)))
        return self
    
    def with_treatment(self, treatment_type: str = None, regimen: str = None) -> 'CohortQueryDSL':
        """Filter by treatment received"""
        if treatment_type:
            self._inclusions.append(Criterion('treatment_type', Operator.EQUALS, treatment_type))
        if regimen:
            self._inclusions.append(Criterion('regimen', Operator.ICONTAINS, regimen))
        return self
    
    def with_mutation(self, *mutations: str) -> 'CohortQueryDSL':
        """Filter by molecular mutations"""
        for mutation in mutations:
            self._inclusions.append(Criterion('mutation', Operator.CONTAINS, mutation))
        return self
    
    def had_relapse(self, is_true: bool = True) -> 'CohortQueryDSL':
        """Filter by relapse status"""
        if is_true:
            self._inclusions.append(Criterion('relapse_count', Operator.GREATER_THAN_OR_EQUAL, 1))
        else:
            self._exclusions.append(Criterion('relapse_count', Operator.GREATER_THAN_OR_EQUAL, 1))
        return self
    
    def with_response(self, *responses: str) -> 'CohortQueryDSL':
        """Filter by treatment response"""
        if len(responses) == 1:
            self._inclusions.append(Criterion('response', Operator.EQUALS, responses[0]))
        else:
            self._inclusions.append(Criterion('response', Operator.IN, list(responses)))
        return self
    
    def output(self, *fields: str) -> 'CohortQueryDSL':
        """Specify output fields"""
        self._output_fields.extend(fields)
        return self
    
    def build(self) -> CohortDefinition:
        """Build the cohort definition"""
        inclusion_group = CriteriaGroup(
            operator=LogicalOperator.AND,
            criteria=self._inclusions
        )
        
        exclusion_group = None
        if self._exclusions:
            exclusion_group = CriteriaGroup(
                operator=LogicalOperator.OR,
                criteria=self._exclusions
            )
        
        return CohortDefinition(
            name=self.name,
            description=self.description,
            inclusion_criteria=inclusion_group,
            exclusion_criteria=exclusion_group,
            output_fields=self._output_fields if self._output_fields else None,
        )
    
    def execute(self) -> CohortBuilder:
        """Build and execute the cohort query"""
        definition = self.build()
        builder = CohortBuilder(definition)
        builder.build_queryset()
        return builder


# Convenience functions for common cohort types
def create_lymphoma_cohort(
    subtype: str = None,
    stages: List[str] = None,
    include_relapsed: bool = True
) -> CohortBuilder:
    """
    Create a lymphoma cohort with common filters
    """
    dsl = CohortQueryDSL("Lymphoma Cohort")
    dsl.include('cancer_category', 'eq', 'Hematologic')
    
    if subtype:
        dsl.cancer_type(subtype)
    else:
        dsl.include('cancer_type', 'icontains', 'lymphoma')
    
    if stages:
        dsl.stage(*stages)
    
    if not include_relapsed:
        dsl.exclude('relapse_count', 'gte', 1)
    
    return dsl.execute()


def create_transplant_cohort(
    transplant_type: str = None,
    cancer_types: List[str] = None
) -> CohortBuilder:
    """
    Create a stem cell transplant cohort
    """
    dsl = CohortQueryDSL("Transplant Cohort")
    dsl.with_treatment('transplant')
    
    if transplant_type:
        dsl.include('transplant_type', 'eq', transplant_type)
    
    if cancer_types:
        dsl.cancer_type(*cancer_types)
    
    return dsl.execute()


def create_car_t_cohort(
    indication: str = None,
    product: str = None
) -> CohortBuilder:
    """
    Create a CAR-T cell therapy cohort
    """
    dsl = CohortQueryDSL("CAR-T Cohort")
    dsl.with_treatment('car_t')
    
    if indication:
        dsl.cancer_type(indication)
    
    if product:
        dsl.include('regimen', 'icontains', product)
    
    return dsl.execute()

