"""
Personalized Medicine Treatment Engine
AI-powered treatment recommendations based on patient characteristics and outcomes data
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime
from enum import Enum
import logging
from decimal import Decimal
import numpy as np
from django.db.models import Count, Avg, Q, F

from oncology.models import (
    Patient, CancerType, CancerDiagnosis, Pathology, Cytogenetics,
    Treatment, TreatmentResponse, Relapse, Outcome, Biomarker,
    Comorbidity
)

logger = logging.getLogger(__name__)


@dataclass
class PatientProfile:
    """
    Comprehensive patient profile for treatment matching
    """
    # Demographics
    age: int
    sex: str
    performance_status: Optional[int] = None  # ECOG PS
    
    # Diagnosis
    cancer_type: str
    cancer_category: str
    stage: str
    histology: Optional[str] = None
    grade: Optional[str] = None
    
    # Molecular profile
    mutations: List[str] = field(default_factory=list)
    molecular_markers: Dict[str, str] = field(default_factory=dict)
    molecular_risk: Optional[str] = None
    ihc_results: Dict[str, str] = field(default_factory=dict)
    
    # Karyotype/Cytogenetics
    karyotype: Optional[str] = None
    cytogenetic_risk: Optional[str] = None
    
    # Prior treatments
    prior_lines: int = 0
    prior_regimens: List[str] = field(default_factory=list)
    prior_responses: Dict[str, str] = field(default_factory=dict)
    had_transplant: bool = False
    had_car_t: bool = False
    
    # Relapse info
    relapse_count: int = 0
    is_refractory: bool = False
    time_since_last_treatment_months: Optional[int] = None
    
    # Comorbidities
    comorbidities: List[str] = field(default_factory=list)
    organ_function: Dict[str, str] = field(default_factory=dict)
    # e.g., {"cardiac": "normal", "renal": "mild_impairment"}
    
    # Biomarkers
    biomarkers: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def from_patient(cls, patient: Patient, diagnosis: CancerDiagnosis) -> 'PatientProfile':
        """
        Build profile from database records
        """
        current_year = datetime.now().year
        
        # Get molecular data
        cyto = diagnosis.cytogenetics.order_by('-test_date').first()
        path = diagnosis.pathology_reports.order_by('-report_date').first()
        
        # Get prior treatments
        treatments = diagnosis.treatments.order_by('start_date')
        prior_regimens = [t.regimen_name for t in treatments]
        prior_responses = {}
        for t in treatments:
            best_resp = t.responses.filter(best_response=True).first()
            if best_resp:
                prior_responses[t.regimen_name] = best_resp.response_type
        
        # Get comorbidities
        comorbidities = list(
            patient.comorbidities.filter(is_active=True)
            .values_list('condition_name', flat=True)
        )
        
        return cls(
            age=current_year - patient.birth_year if patient.birth_year else 0,
            sex=patient.sex,
            performance_status=diagnosis.ecog_ps,
            cancer_type=diagnosis.cancer_type.name,
            cancer_category=diagnosis.cancer_type.category,
            stage=diagnosis.clinical_stage or diagnosis.pathologic_stage,
            histology=path.histology if path else None,
            grade=path.histologic_grade if path else None,
            mutations=cyto.mutations_detected if cyto else [],
            molecular_markers=cyto.molecular_markers if cyto else {},
            molecular_risk=cyto.molecular_risk_group if cyto else None,
            ihc_results=path.ihc_results if path else {},
            karyotype=cyto.karyotype if cyto else None,
            prior_lines=treatments.count(),
            prior_regimens=prior_regimens,
            prior_responses=prior_responses,
            had_transplant=treatments.filter(treatment_type='transplant').exists(),
            had_car_t=treatments.filter(treatment_type='car_t').exists(),
            relapse_count=diagnosis.relapses.count(),
            is_refractory=diagnosis.relapses.filter(is_refractory=True).exists(),
            comorbidities=comorbidities,
        )


@dataclass
class TreatmentRecommendation:
    """
    A treatment recommendation with supporting evidence
    """
    regimen_name: str
    treatment_type: str
    confidence_score: float  # 0-1
    
    # Predicted outcomes
    predicted_response_rate: float
    predicted_cr_rate: float
    predicted_pfs_months: Optional[float] = None
    predicted_os_months: Optional[float] = None
    
    # Evidence
    evidence_level: str  # "NCCN", "clinical_trial", "real_world"
    supporting_patients: int  # Number of similar patients
    similar_patient_outcomes: Dict[str, float] = field(default_factory=dict)
    
    # Clinical trial matches
    matching_trials: List[str] = field(default_factory=list)
    
    # Considerations
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    monitoring_requirements: List[str] = field(default_factory=list)
    
    # Molecular rationale
    targeted_mutations: List[str] = field(default_factory=list)
    biomarker_rationale: str = ""


class TreatmentMatchingEngine:
    """
    Matches patients to optimal treatments based on characteristics and outcomes
    """
    
    # Treatment guidelines by cancer type
    STANDARD_REGIMENS = {
        'Diffuse Large B-Cell Lymphoma': {
            'first_line': ['R-CHOP', 'Pola-R-CHP', 'R-EPOCH'],
            'second_line': ['R-ICE', 'R-DHAP', 'R-GDP', 'CAR-T'],
            'third_line': ['CAR-T', 'Loncastuximab', 'Selinexor'],
        },
        'Acute Myeloid Leukemia': {
            'first_line': ['7+3', 'CPX-351', 'Venetoclax+Azacitidine', 'Venetoclax+LDAC'],
            'second_line': ['MEC', 'FLAG-IDA', 'Gilteritinib', 'Enasidenib'],
        },
        'Multiple Myeloma': {
            'first_line': ['VRd', 'DRd', 'KRd', 'DVRd'],
            'second_line': ['Dara-Pd', 'Kd', 'IRd', 'Elo-Pd'],
            'third_line': ['CAR-T', 'Teclistamab', 'Talquetamab', 'Elranatamab'],
        },
    }
    
    # Molecular-targeted treatments
    MOLECULAR_TARGETS = {
        'FLT3-ITD': ['Midostaurin', 'Gilteritinib', 'Quizartinib'],
        'FLT3-TKD': ['Midostaurin', 'Gilteritinib'],
        'IDH1': ['Ivosidenib', 'Olutasidenib'],
        'IDH2': ['Enasidenib'],
        'NPM1': ['Menin inhibitors'],
        'BCR-ABL': ['Imatinib', 'Dasatinib', 'Nilotinib', 'Ponatinib'],
        'BRAF V600E': ['Vemurafenib+Cobimetinib', 'Dabrafenib+Trametinib'],
        'HER2+': ['Trastuzumab', 'Pertuzumab', 'T-DM1', 'T-DXd'],
        'EGFR': ['Osimertinib', 'Erlotinib', 'Gefitinib'],
        'ALK': ['Alectinib', 'Brigatinib', 'Lorlatinib'],
        'PD-L1 High': ['Pembrolizumab', 'Nivolumab', 'Atezolizumab'],
    }
    
    def __init__(self):
        self.similarity_threshold = 0.7
    
    def get_recommendations(
        self,
        profile: PatientProfile,
        max_recommendations: int = 5
    ) -> List[TreatmentRecommendation]:
        """
        Generate treatment recommendations for a patient
        """
        recommendations = []
        
        # 1. Get standard of care recommendations
        standard_recs = self._get_standard_care_recommendations(profile)
        recommendations.extend(standard_recs)
        
        # 2. Get molecular-targeted recommendations
        molecular_recs = self._get_molecular_recommendations(profile)
        recommendations.extend(molecular_recs)
        
        # 3. Find similar patients and their outcomes
        similar_patients = self._find_similar_patients(profile)
        real_world_recs = self._get_real_world_recommendations(profile, similar_patients)
        recommendations.extend(real_world_recs)
        
        # 4. Score and rank recommendations
        scored_recs = self._score_recommendations(recommendations, profile)
        
        # 5. Deduplicate and sort
        unique_recs = self._deduplicate_recommendations(scored_recs)
        sorted_recs = sorted(unique_recs, key=lambda x: x.confidence_score, reverse=True)
        
        return sorted_recs[:max_recommendations]
    
    def _get_standard_care_recommendations(
        self,
        profile: PatientProfile
    ) -> List[TreatmentRecommendation]:
        """
        Get standard of care recommendations based on guidelines
        """
        recommendations = []
        
        cancer_regimens = self.STANDARD_REGIMENS.get(profile.cancer_type, {})
        
        # Determine treatment line
        if profile.prior_lines == 0:
            line = 'first_line'
        elif profile.prior_lines == 1:
            line = 'second_line'
        else:
            line = 'third_line'
        
        regimens = cancer_regimens.get(line, [])
        
        for regimen in regimens:
            # Check eligibility
            eligible, reasons = self._check_eligibility(regimen, profile)
            
            if eligible:
                # Get historical outcomes for this regimen
                outcomes = self._get_regimen_outcomes(regimen, profile)
                
                rec = TreatmentRecommendation(
                    regimen_name=regimen,
                    treatment_type=self._infer_treatment_type(regimen),
                    confidence_score=0.8,  # High confidence for standard care
                    predicted_response_rate=outcomes.get('orr', 0.7),
                    predicted_cr_rate=outcomes.get('cr_rate', 0.5),
                    predicted_pfs_months=outcomes.get('median_pfs'),
                    predicted_os_months=outcomes.get('median_os'),
                    evidence_level='NCCN',
                    supporting_patients=outcomes.get('n', 0),
                    pros=self._get_regimen_pros(regimen, profile),
                    cons=self._get_regimen_cons(regimen, profile),
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _get_molecular_recommendations(
        self,
        profile: PatientProfile
    ) -> List[TreatmentRecommendation]:
        """
        Get recommendations based on molecular/genetic features
        """
        recommendations = []
        
        # Check for targetable mutations
        for mutation in profile.mutations:
            targets = self.MOLECULAR_TARGETS.get(mutation, [])
            
            for drug in targets:
                outcomes = self._get_targeted_outcomes(drug, mutation, profile)
                
                rec = TreatmentRecommendation(
                    regimen_name=drug,
                    treatment_type='targeted_therapy',
                    confidence_score=0.85,
                    predicted_response_rate=outcomes.get('orr', 0.6),
                    predicted_cr_rate=outcomes.get('cr_rate', 0.4),
                    predicted_pfs_months=outcomes.get('median_pfs'),
                    evidence_level='clinical_trial',
                    supporting_patients=outcomes.get('n', 0),
                    targeted_mutations=[mutation],
                    biomarker_rationale=f"Patient has {mutation} mutation which is targetable by {drug}",
                    pros=[f"Targets {mutation} mutation specifically", "Generally well-tolerated"],
                    cons=["May develop resistance over time"],
                )
                recommendations.append(rec)
        
        # Check molecular markers
        for marker, value in profile.molecular_markers.items():
            if marker in self.MOLECULAR_TARGETS:
                targets = self.MOLECULAR_TARGETS[marker]
                for drug in targets:
                    rec = TreatmentRecommendation(
                        regimen_name=drug,
                        treatment_type='targeted_therapy',
                        confidence_score=0.8,
                        predicted_response_rate=0.6,
                        predicted_cr_rate=0.35,
                        evidence_level='clinical_trial',
                        supporting_patients=50,
                        targeted_mutations=[marker],
                        biomarker_rationale=f"Patient is {marker} positive",
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    def _find_similar_patients(
        self,
        profile: PatientProfile,
        max_patients: int = 100
    ) -> List[Tuple[Patient, float]]:
        """
        Find patients with similar characteristics
        Returns list of (patient, similarity_score) tuples
        """
        # Build query for similar patients
        similar = CancerDiagnosis.objects.filter(
            cancer_type__name=profile.cancer_type,
        )
        
        # Filter by age range (+/- 10 years)
        current_year = datetime.now().year
        similar = similar.filter(
            patient__birth_year__gte=current_year - profile.age - 10,
            patient__birth_year__lte=current_year - profile.age + 10,
        )
        
        # Filter by stage if available
        if profile.stage:
            similar = similar.filter(
                Q(clinical_stage=profile.stage) | Q(pathologic_stage=profile.stage)
            )
        
        # Filter by treatment line
        similar = similar.annotate(
            treatment_count=Count('treatments')
        ).filter(treatment_count__gte=profile.prior_lines)
        
        # Calculate similarity scores
        similar_patients = []
        for diagnosis in similar[:max_patients]:
            score = self._calculate_similarity(profile, diagnosis)
            if score >= self.similarity_threshold:
                similar_patients.append((diagnosis.patient, score))
        
        return sorted(similar_patients, key=lambda x: x[1], reverse=True)
    
    def _calculate_similarity(
        self,
        profile: PatientProfile,
        diagnosis: CancerDiagnosis
    ) -> float:
        """
        Calculate similarity score between patient profile and a diagnosis
        """
        score = 0.0
        factors = 0
        
        # Cancer type match (must match)
        if diagnosis.cancer_type.name != profile.cancer_type:
            return 0.0
        score += 1.0
        factors += 1
        
        # Age similarity
        current_year = datetime.now().year
        patient_age = current_year - diagnosis.patient.birth_year if diagnosis.patient.birth_year else 0
        age_diff = abs(patient_age - profile.age)
        age_score = max(0, 1 - (age_diff / 20))  # Full score if within 0 years, 0 if 20+ years diff
        score += age_score
        factors += 1
        
        # Stage match
        if profile.stage and diagnosis.clinical_stage:
            if diagnosis.clinical_stage == profile.stage:
                score += 1.0
            elif diagnosis.clinical_stage[0] == profile.stage[0]:  # Same roman numeral
                score += 0.5
        factors += 1
        
        # Sex match
        if diagnosis.patient.sex == profile.sex:
            score += 0.5
        factors += 0.5
        
        # Molecular features (if available)
        cyto = diagnosis.cytogenetics.first()
        if cyto and profile.mutations:
            matching_mutations = set(cyto.mutations_detected or []) & set(profile.mutations)
            if matching_mutations:
                score += len(matching_mutations) / max(len(profile.mutations), 1)
            factors += 1
        
        # Prior lines match
        treatment_count = diagnosis.treatments.count()
        if treatment_count == profile.prior_lines:
            score += 1.0
        elif abs(treatment_count - profile.prior_lines) == 1:
            score += 0.5
        factors += 1
        
        return score / factors if factors > 0 else 0.0
    
    def _get_real_world_recommendations(
        self,
        profile: PatientProfile,
        similar_patients: List[Tuple[Patient, float]]
    ) -> List[TreatmentRecommendation]:
        """
        Get recommendations based on real-world outcomes of similar patients
        """
        recommendations = []
        
        if not similar_patients:
            return recommendations
        
        # Aggregate treatment outcomes from similar patients
        regimen_outcomes = {}
        
        for patient, similarity in similar_patients:
            for diagnosis in patient.diagnoses.all():
                for treatment in diagnosis.treatments.all():
                    regimen = treatment.regimen_name
                    
                    if regimen not in regimen_outcomes:
                        regimen_outcomes[regimen] = {
                            'patients': [],
                            'responses': [],
                            'pfs': [],
                            'os': [],
                        }
                    
                    regimen_outcomes[regimen]['patients'].append(similarity)
                    
                    # Get best response
                    best_resp = treatment.responses.filter(best_response=True).first()
                    if best_resp:
                        regimen_outcomes[regimen]['responses'].append(best_resp.response_type)
                    
                    # Get survival outcomes
                    outcome = diagnosis.outcomes.order_by('-last_followup_date').first()
                    if outcome:
                        if outcome.progression_free_survival_months:
                            regimen_outcomes[regimen]['pfs'].append(
                                outcome.progression_free_survival_months
                            )
                        if outcome.overall_survival_months:
                            regimen_outcomes[regimen]['os'].append(
                                outcome.overall_survival_months
                            )
        
        # Create recommendations from aggregated data
        for regimen, data in regimen_outcomes.items():
            n_patients = len(data['patients'])
            if n_patients < 3:  # Require at least 3 similar patients
                continue
            
            # Calculate response rates
            responses = data['responses']
            cr_count = sum(1 for r in responses if r in ['cr', 'cru'])
            pr_count = sum(1 for r in responses if r == 'pr')
            orr = (cr_count + pr_count) / len(responses) if responses else 0
            cr_rate = cr_count / len(responses) if responses else 0
            
            # Calculate survival
            median_pfs = np.median(data['pfs']) if data['pfs'] else None
            median_os = np.median(data['os']) if data['os'] else None
            
            # Weight by similarity
            avg_similarity = np.mean(data['patients'])
            
            rec = TreatmentRecommendation(
                regimen_name=regimen,
                treatment_type=self._infer_treatment_type(regimen),
                confidence_score=avg_similarity * 0.7,  # Scale by similarity
                predicted_response_rate=orr,
                predicted_cr_rate=cr_rate,
                predicted_pfs_months=median_pfs,
                predicted_os_months=median_os,
                evidence_level='real_world',
                supporting_patients=n_patients,
                similar_patient_outcomes={
                    'orr': orr,
                    'cr_rate': cr_rate,
                    'median_pfs': median_pfs,
                    'median_os': median_os,
                },
                pros=[f"Based on outcomes from {n_patients} similar patients"],
                cons=["Real-world evidence may have selection bias"],
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _check_eligibility(
        self,
        regimen: str,
        profile: PatientProfile
    ) -> Tuple[bool, List[str]]:
        """
        Check if patient is eligible for a regimen
        Returns (eligible, list of reasons if not eligible)
        """
        reasons = []
        
        # Check performance status
        if profile.performance_status is not None and profile.performance_status > 2:
            if regimen in ['R-EPOCH', '7+3', 'CPX-351', 'MEC']:
                reasons.append("Performance status too low for intensive regimen")
        
        # Check age
        if profile.age > 75:
            if regimen in ['7+3', 'CPX-351', 'R-EPOCH']:
                reasons.append("Age may preclude intensive regimen")
        
        # Check prior treatments
        if 'CAR-T' in regimen:
            if not profile.had_transplant and profile.prior_lines < 2:
                reasons.append("May need at least 2 prior lines for CAR-T")
        
        # Check for specific comorbidities
        cardiac_issues = any('cardiac' in c.lower() or 'heart' in c.lower() 
                           for c in profile.comorbidities)
        if cardiac_issues and regimen in ['R-CHOP', 'VRd']:
            reasons.append("Cardiac comorbidity - consider anthracycline-sparing regimen")
        
        return len(reasons) == 0, reasons
    
    def _get_regimen_outcomes(
        self,
        regimen: str,
        profile: PatientProfile
    ) -> Dict[str, float]:
        """
        Get historical outcomes for a regimen
        """
        treatments = Treatment.objects.filter(
            regimen_name__icontains=regimen,
            diagnosis__cancer_type__name=profile.cancer_type,
        )
        
        n = treatments.count()
        if n == 0:
            return {'n': 0, 'orr': 0.7, 'cr_rate': 0.5}  # Default values
        
        # Calculate response rates
        responses = TreatmentResponse.objects.filter(
            treatment__in=treatments,
            best_response=True
        )
        
        cr_count = responses.filter(response_type__in=['cr', 'cru']).count()
        pr_count = responses.filter(response_type='pr').count()
        total_responses = responses.count()
        
        orr = (cr_count + pr_count) / total_responses if total_responses else 0.7
        cr_rate = cr_count / total_responses if total_responses else 0.5
        
        # Get survival data
        outcomes = Outcome.objects.filter(
            diagnosis__treatments__in=treatments
        ).distinct()
        
        pfs_values = list(outcomes.values_list('progression_free_survival_months', flat=True))
        os_values = list(outcomes.values_list('overall_survival_months', flat=True))
        
        return {
            'n': n,
            'orr': orr,
            'cr_rate': cr_rate,
            'median_pfs': np.median([v for v in pfs_values if v]) if pfs_values else None,
            'median_os': np.median([v for v in os_values if v]) if os_values else None,
        }
    
    def _get_targeted_outcomes(
        self,
        drug: str,
        mutation: str,
        profile: PatientProfile
    ) -> Dict[str, float]:
        """
        Get outcomes for targeted therapy in mutation-positive patients
        """
        # Find patients with this mutation treated with this drug
        treatments = Treatment.objects.filter(
            regimen_name__icontains=drug,
            diagnosis__cytogenetics__mutations_detected__contains=[mutation],
        )
        
        n = treatments.count()
        if n == 0:
            return {'n': 0, 'orr': 0.6, 'cr_rate': 0.4}
        
        responses = TreatmentResponse.objects.filter(
            treatment__in=treatments,
            best_response=True
        )
        
        total = responses.count()
        cr_count = responses.filter(response_type__in=['cr', 'cru']).count()
        pr_count = responses.filter(response_type='pr').count()
        
        return {
            'n': n,
            'orr': (cr_count + pr_count) / total if total else 0.6,
            'cr_rate': cr_count / total if total else 0.4,
        }
    
    def _score_recommendations(
        self,
        recommendations: List[TreatmentRecommendation],
        profile: PatientProfile
    ) -> List[TreatmentRecommendation]:
        """
        Score and adjust recommendation confidence based on profile
        """
        for rec in recommendations:
            # Boost score for molecular matches
            if rec.targeted_mutations:
                matching = set(rec.targeted_mutations) & set(profile.mutations)
                if matching:
                    rec.confidence_score = min(1.0, rec.confidence_score + 0.1)
            
            # Boost score for high patient count
            if rec.supporting_patients > 50:
                rec.confidence_score = min(1.0, rec.confidence_score + 0.05)
            
            # Reduce score if patient has had this regimen before
            if rec.regimen_name in profile.prior_regimens:
                prior_response = profile.prior_responses.get(rec.regimen_name)
                if prior_response in ['cr', 'cru', 'pr']:
                    rec.confidence_score *= 0.9  # Slight reduction for retreatment
                else:
                    rec.confidence_score *= 0.5  # Significant reduction if didn't respond
        
        return recommendations
    
    def _deduplicate_recommendations(
        self,
        recommendations: List[TreatmentRecommendation]
    ) -> List[TreatmentRecommendation]:
        """
        Remove duplicate recommendations, keeping highest scored
        """
        seen = {}
        for rec in recommendations:
            key = rec.regimen_name.lower()
            if key not in seen or rec.confidence_score > seen[key].confidence_score:
                seen[key] = rec
        return list(seen.values())
    
    def _infer_treatment_type(self, regimen: str) -> str:
        """
        Infer treatment type from regimen name
        """
        regimen_lower = regimen.lower()
        
        if any(x in regimen_lower for x in ['car-t', 'yescarta', 'kymriah', 'tecartus', 'breyanzi']):
            return 'car_t'
        if any(x in regimen_lower for x in ['transplant', 'auto', 'allo']):
            return 'transplant'
        if any(x in regimen_lower for x in ['pembrolizumab', 'nivolumab', 'ipilimumab', 'atezolizumab']):
            return 'immunotherapy'
        if any(x in regimen_lower for x in ['radiation', 'xrt', 'imrt']):
            return 'radiation'
        if any(x in regimen_lower for x in ['surgery', 'resection', 'excision']):
            return 'surgery'
        if any(x in regimen_lower for x in ['venetoclax', 'ibrutinib', 'acalabrutinib', 'imatinib', 
                                             'osimertinib', 'alectinib', 'gilteritinib']):
            return 'targeted_therapy'
        
        return 'chemotherapy'
    
    def _get_regimen_pros(self, regimen: str, profile: PatientProfile) -> List[str]:
        """
        Get pros/advantages of a regimen for this patient
        """
        pros = []
        
        if 'R-CHOP' in regimen:
            pros.append("Standard of care with extensive experience")
            pros.append("Outpatient administration possible")
        elif 'Venetoclax' in regimen:
            pros.append("Oral administration")
            pros.append("Good option for older/unfit patients")
        elif 'CAR-T' in regimen:
            pros.append("Potentially curative for relapsed/refractory disease")
            pros.append("One-time treatment")
        
        return pros
    
    def _get_regimen_cons(self, regimen: str, profile: PatientProfile) -> List[str]:
        """
        Get cons/disadvantages of a regimen for this patient
        """
        cons = []
        
        if any(x in regimen for x in ['7+3', 'CPX-351', 'MEC', 'FLAG']):
            cons.append("Requires prolonged hospitalization")
            cons.append("High risk of infection during neutropenia")
        elif 'CAR-T' in regimen:
            cons.append("Risk of cytokine release syndrome (CRS)")
            cons.append("Risk of neurotoxicity (ICANS)")
            cons.append("Limited availability at specialized centers")
        
        if profile.age > 65:
            if any(x in regimen for x in ['CHOP', 'EPOCH', '7+3']):
                cons.append("May have increased toxicity in older patients")
        
        return cons


class OutcomePredictionEngine:
    """
    Predict treatment outcomes using machine learning models
    """
    
    def predict_response(
        self,
        profile: PatientProfile,
        regimen: str
    ) -> Dict[str, float]:
        """
        Predict response probability for a regimen
        Returns probabilities for each response category
        """
        # This would use a trained ML model
        # Placeholder implementation using heuristics
        
        base_rates = {
            'cr': 0.45,
            'pr': 0.25,
            'sd': 0.15,
            'pd': 0.15,
        }
        
        # Adjust based on molecular features
        if profile.molecular_risk == 'favorable':
            base_rates['cr'] += 0.1
            base_rates['pd'] -= 0.1
        elif profile.molecular_risk == 'adverse':
            base_rates['cr'] -= 0.15
            base_rates['pd'] += 0.15
        
        # Adjust based on treatment line
        line_adjustment = 0.05 * profile.prior_lines
        base_rates['cr'] -= line_adjustment
        base_rates['pd'] += line_adjustment
        
        # Normalize
        total = sum(base_rates.values())
        return {k: v/total for k, v in base_rates.items()}
    
    def predict_survival(
        self,
        profile: PatientProfile,
        regimen: str
    ) -> Dict[str, Any]:
        """
        Predict survival outcomes
        Returns predicted PFS and OS with confidence intervals
        """
        # This would use a trained survival model
        # Placeholder implementation
        
        base_pfs = 18.0  # months
        base_os = 36.0   # months
        
        # Adjust based on features
        if profile.molecular_risk == 'favorable':
            base_pfs *= 1.3
            base_os *= 1.4
        elif profile.molecular_risk == 'adverse':
            base_pfs *= 0.6
            base_os *= 0.7
        
        if profile.performance_status and profile.performance_status > 1:
            base_pfs *= 0.8
            base_os *= 0.8
        
        return {
            'median_pfs_months': base_pfs,
            'pfs_ci_lower': base_pfs * 0.7,
            'pfs_ci_upper': base_pfs * 1.3,
            'median_os_months': base_os,
            'os_ci_lower': base_os * 0.7,
            'os_ci_upper': base_os * 1.3,
            'pfs_probability_12m': 0.6,
            'os_probability_12m': 0.85,
        }

