"""
Comprehensive Oncology Data Models for Longitudinal Cancer Database
Supports EMR integration, retrospective studies, and personalized medicine
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from data_collection.models import Institution
from accounts.models import User
import uuid


class Patient(models.Model):
    """
    De-identified patient record - the MRN is hashed, never stored raw.
    Patients can optionally link their accounts for data sharing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hashed_mrn = models.CharField(max_length=128, unique=True, db_index=True)
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT)
    
    # Demographics (de-identified where needed)
    birth_year = models.IntegerField(null=True)  # Only year, not full DOB
    sex = models.CharField(max_length=20, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown')
    ])
    race = models.CharField(max_length=50, null=True, blank=True)
    ethnicity = models.CharField(max_length=50, null=True, blank=True)
    
    # Patient portal linkage (optional)
    linked_user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='patient_record'
    )
    consent_date = models.DateTimeField(null=True, blank=True)
    data_sharing_level = models.CharField(max_length=20, choices=[
        ('none', 'No Sharing'),
        ('research_only', 'Research Only'),
        ('full', 'Full Access'),
    ], default='none')
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_emr_sync = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['hashed_mrn', 'institution']),
            models.Index(fields=['birth_year', 'sex']),
        ]


class CancerType(models.Model):
    """
    Master list of cancer types with ICD-O-3 morphology codes
    """
    icd_o3_code = models.CharField(max_length=10, unique=True)
    icd10_code = models.CharField(max_length=10, null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)  # e.g., "Hematologic", "Solid Tumor"
    subcategory = models.CharField(max_length=100, null=True, blank=True)
    
    # Data collection template
    required_fields = models.JSONField(default=dict)  # JSON Schema
    optional_fields = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['category', 'name']


class CancerDiagnosis(models.Model):
    """
    Primary cancer diagnosis with staging and molecular details
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='diagnoses')
    cancer_type = models.ForeignKey(CancerType, on_delete=models.PROTECT)
    
    # Diagnosis details
    diagnosis_date = models.DateField()
    age_at_diagnosis = models.IntegerField(null=True)
    
    # Staging (AJCC 8th edition)
    clinical_stage = models.CharField(max_length=20, null=True, blank=True)
    pathologic_stage = models.CharField(max_length=20, null=True, blank=True)
    t_stage = models.CharField(max_length=10, null=True, blank=True)
    n_stage = models.CharField(max_length=10, null=True, blank=True)
    m_stage = models.CharField(max_length=10, null=True, blank=True)
    
    # Disease-specific staging (e.g., Ann Arbor for lymphoma)
    disease_specific_stage = models.CharField(max_length=50, null=True, blank=True)
    disease_specific_staging_system = models.CharField(max_length=100, null=True, blank=True)
    
    # Risk stratification
    risk_group = models.CharField(max_length=50, null=True, blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    risk_scoring_system = models.CharField(max_length=100, null=True, blank=True)
    
    # Performance status
    ecog_ps = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    karnofsky_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Site-specific data
    primary_site = models.CharField(max_length=100, null=True, blank=True)
    laterality = models.CharField(max_length=20, choices=[
        ('left', 'Left'),
        ('right', 'Right'),
        ('bilateral', 'Bilateral'),
        ('na', 'Not Applicable'),
    ], null=True, blank=True)
    
    # Data provenance
    source_emr = models.CharField(max_length=50, null=True, blank=True)
    irb_protocol = models.ForeignKey(
        'irb_portal.IRBProtocol', on_delete=models.PROTECT, null=True, blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-diagnosis_date']
        indexes = [
            models.Index(fields=['patient', 'diagnosis_date']),
            models.Index(fields=['cancer_type', 'clinical_stage']),
        ]


class Pathology(models.Model):
    """
    Pathology reports and findings
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagnosis = models.ForeignKey(CancerDiagnosis, on_delete=models.CASCADE, related_name='pathology_reports')
    
    report_date = models.DateField()
    specimen_type = models.CharField(max_length=100)
    specimen_site = models.CharField(max_length=100, null=True, blank=True)
    
    # Histology
    histology = models.CharField(max_length=255)
    histologic_grade = models.CharField(max_length=50, null=True, blank=True)
    differentiation = models.CharField(max_length=50, null=True, blank=True)
    
    # Margins (for surgical specimens)
    margin_status = models.CharField(max_length=50, choices=[
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('close', 'Close (<2mm)'),
        ('unknown', 'Unknown'),
    ], null=True, blank=True)
    
    # Immunohistochemistry results (stored as JSON for flexibility)
    ihc_results = models.JSONField(default=dict)  # e.g., {"ER": "+", "PR": "-", "HER2": "2+"}
    
    # Additional findings
    lymphovascular_invasion = models.BooleanField(null=True)
    perineural_invasion = models.BooleanField(null=True)
    tumor_infiltrating_lymphocytes = models.CharField(max_length=50, null=True, blank=True)
    
    # Full report (de-identified)
    report_text = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


class Cytogenetics(models.Model):
    """
    Cytogenetic and molecular testing results
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagnosis = models.ForeignKey(CancerDiagnosis, on_delete=models.CASCADE, related_name='cytogenetics')
    
    test_date = models.DateField()
    test_type = models.CharField(max_length=100)  # FISH, Karyotype, NGS, etc.
    specimen_type = models.CharField(max_length=100)
    
    # Karyotype
    karyotype = models.TextField(null=True, blank=True)
    ploidy = models.CharField(max_length=50, null=True, blank=True)
    
    # FISH results
    fish_results = models.JSONField(default=dict)  # e.g., {"BCR-ABL": "Positive", "MYC": "Negative"}
    
    # Molecular markers
    molecular_markers = models.JSONField(default=dict)  # e.g., {"FLT3-ITD": "Positive", "NPM1": "Mutated"}
    
    # NGS / Sequencing results
    mutations_detected = ArrayField(
        models.CharField(max_length=100),
        default=list, blank=True
    )
    variant_details = models.JSONField(default=dict)  # Detailed variant info
    tumor_mutational_burden = models.FloatField(null=True, blank=True)
    microsatellite_instability = models.CharField(max_length=20, choices=[
        ('mss', 'MSS'),
        ('msi-l', 'MSI-Low'),
        ('msi-h', 'MSI-High'),
        ('unknown', 'Unknown'),
    ], null=True, blank=True)
    
    # Risk classification from molecular data
    molecular_risk_group = models.CharField(max_length=50, null=True, blank=True)
    
    # Lab and accession info
    performing_lab = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


class Treatment(models.Model):
    """
    Treatment episodes including chemotherapy, radiation, surgery, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagnosis = models.ForeignKey(CancerDiagnosis, on_delete=models.CASCADE, related_name='treatments')
    
    TREATMENT_TYPES = [
        ('chemotherapy', 'Chemotherapy'),
        ('immunotherapy', 'Immunotherapy'),
        ('targeted_therapy', 'Targeted Therapy'),
        ('radiation', 'Radiation Therapy'),
        ('surgery', 'Surgery'),
        ('transplant', 'Stem Cell Transplant'),
        ('car_t', 'CAR-T Cell Therapy'),
        ('hormone_therapy', 'Hormone Therapy'),
        ('other', 'Other'),
    ]
    
    TREATMENT_INTENTS = [
        ('curative', 'Curative'),
        ('palliative', 'Palliative'),
        ('neoadjuvant', 'Neoadjuvant'),
        ('adjuvant', 'Adjuvant'),
        ('consolidation', 'Consolidation'),
        ('maintenance', 'Maintenance'),
        ('salvage', 'Salvage'),
    ]
    
    treatment_type = models.CharField(max_length=50, choices=TREATMENT_TYPES)
    treatment_intent = models.CharField(max_length=50, choices=TREATMENT_INTENTS, null=True, blank=True)
    
    # Treatment line (1st line, 2nd line, etc.)
    treatment_line = models.IntegerField(default=1)
    is_relapse_treatment = models.BooleanField(default=False)
    
    # Regimen details
    regimen_name = models.CharField(max_length=255)  # e.g., "R-CHOP", "FOLFOX", "Pembrolizumab"
    regimen_protocol = models.CharField(max_length=255, null=True, blank=True)
    
    # Timing
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    planned_cycles = models.IntegerField(null=True, blank=True)
    completed_cycles = models.IntegerField(null=True, blank=True)
    
    # Treatment details stored as JSON for flexibility
    drugs = models.JSONField(default=list)  # List of drugs with doses
    # Example: [{"name": "Rituximab", "dose": "375", "unit": "mg/m2", "route": "IV"}]
    
    # For surgery
    surgery_type = models.CharField(max_length=255, null=True, blank=True)
    surgical_approach = models.CharField(max_length=100, null=True, blank=True)
    
    # For radiation
    radiation_site = models.CharField(max_length=255, null=True, blank=True)
    radiation_dose_gy = models.FloatField(null=True, blank=True)
    radiation_fractions = models.IntegerField(null=True, blank=True)
    
    # For transplant
    transplant_type = models.CharField(max_length=50, choices=[
        ('autologous', 'Autologous'),
        ('allogeneic', 'Allogeneic'),
    ], null=True, blank=True)
    donor_type = models.CharField(max_length=50, null=True, blank=True)
    conditioning_regimen = models.CharField(max_length=255, null=True, blank=True)
    
    # Notes and additional data
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['diagnosis', 'treatment_line', 'start_date']
        indexes = [
            models.Index(fields=['diagnosis', 'treatment_type']),
            models.Index(fields=['regimen_name']),
        ]


class TreatmentResponse(models.Model):
    """
    Response assessment for treatments
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='responses')
    
    assessment_date = models.DateField()
    
    # Response categories (RECIST, Lugano, etc.)
    RESPONSE_TYPES = [
        ('cr', 'Complete Response'),
        ('pr', 'Partial Response'),
        ('sd', 'Stable Disease'),
        ('pd', 'Progressive Disease'),
        ('cru', 'Complete Response Unconfirmed'),
        ('mrd_neg', 'MRD Negative'),
        ('mrd_pos', 'MRD Positive'),
        ('ne', 'Not Evaluable'),
    ]
    
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    response_criteria = models.CharField(max_length=50)  # RECIST 1.1, Lugano, IMWG, etc.
    
    # Measurable disease assessment
    best_response = models.BooleanField(default=False)  # Is this the best response?
    
    # MRD assessment
    mrd_assessed = models.BooleanField(default=False)
    mrd_method = models.CharField(max_length=100, null=True, blank=True)
    mrd_sensitivity = models.CharField(max_length=50, null=True, blank=True)
    mrd_result = models.CharField(max_length=50, null=True, blank=True)
    
    # Additional response data
    response_details = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)


class Relapse(models.Model):
    """
    Disease relapse/progression events
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagnosis = models.ForeignKey(CancerDiagnosis, on_delete=models.CASCADE, related_name='relapses')
    
    relapse_date = models.DateField()
    relapse_number = models.IntegerField(default=1)  # 1st relapse, 2nd relapse, etc.
    
    # Time from diagnosis/treatment
    months_from_diagnosis = models.IntegerField(null=True, blank=True)
    months_from_last_treatment = models.IntegerField(null=True, blank=True)
    
    # Relapse details
    relapse_site = ArrayField(
        models.CharField(max_length=100),
        default=list, blank=True
    )
    is_refractory = models.BooleanField(default=False)  # Primary refractory
    is_transformed = models.BooleanField(default=False)  # Disease transformation
    transformed_histology = models.CharField(max_length=255, null=True, blank=True)
    
    # Molecular changes at relapse
    new_mutations = ArrayField(
        models.CharField(max_length=100),
        default=list, blank=True
    )
    
    # Notes
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['diagnosis', 'relapse_number']


class Outcome(models.Model):
    """
    Patient outcomes and survival data
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='outcomes')
    diagnosis = models.ForeignKey(CancerDiagnosis, on_delete=models.CASCADE, related_name='outcomes')
    
    # Vital status
    vital_status = models.CharField(max_length=20, choices=[
        ('alive', 'Alive'),
        ('deceased', 'Deceased'),
        ('lost_to_followup', 'Lost to Follow-up'),
        ('unknown', 'Unknown'),
    ])
    
    last_known_alive_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    cause_of_death = models.CharField(max_length=255, null=True, blank=True)
    death_related_to_cancer = models.BooleanField(null=True)
    death_related_to_treatment = models.BooleanField(null=True)
    
    # Disease status at last follow-up
    disease_status = models.CharField(max_length=50, choices=[
        ('no_evidence', 'No Evidence of Disease'),
        ('active', 'Active Disease'),
        ('stable', 'Stable Disease'),
        ('progression', 'Progression'),
        ('unknown', 'Unknown'),
    ], null=True, blank=True)
    
    # Calculated survival times (in months)
    overall_survival_months = models.FloatField(null=True, blank=True)
    progression_free_survival_months = models.FloatField(null=True, blank=True)
    event_free_survival_months = models.FloatField(null=True, blank=True)
    
    # Last follow-up
    last_followup_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Biomarker(models.Model):
    """
    Longitudinal biomarker tracking (labs, tumor markers, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='biomarkers')
    diagnosis = models.ForeignKey(CancerDiagnosis, on_delete=models.CASCADE, null=True, blank=True)
    
    test_date = models.DateField()
    biomarker_name = models.CharField(max_length=100, db_index=True)
    biomarker_category = models.CharField(max_length=50)  # "tumor_marker", "lab", "imaging_marker"
    
    value = models.FloatField(null=True, blank=True)
    value_string = models.CharField(max_length=255, null=True, blank=True)  # For non-numeric values
    unit = models.CharField(max_length=50, null=True, blank=True)
    reference_range = models.CharField(max_length=100, null=True, blank=True)
    is_abnormal = models.BooleanField(null=True)
    
    # Context
    timepoint = models.CharField(max_length=50, null=True, blank=True)  # "baseline", "post_treatment", etc.
    related_treatment = models.ForeignKey(Treatment, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['patient', 'biomarker_name', 'test_date']),
        ]


class AdverseEvent(models.Model):
    """
    Treatment-related adverse events (CTCAE graded)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='adverse_events')
    
    event_term = models.CharField(max_length=255)  # MedDRA preferred term
    ctcae_category = models.CharField(max_length=100)
    ctcae_grade = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    onset_date = models.DateField()
    resolution_date = models.DateField(null=True, blank=True)
    
    is_serious = models.BooleanField(default=False)
    action_taken = models.CharField(max_length=100, null=True, blank=True)  # "dose_reduced", "discontinued", etc.
    outcome = models.CharField(max_length=100, null=True, blank=True)
    
    # Attribution
    attribution_to_treatment = models.CharField(max_length=50, choices=[
        ('unrelated', 'Unrelated'),
        ('unlikely', 'Unlikely'),
        ('possible', 'Possible'),
        ('probable', 'Probable'),
        ('definite', 'Definite'),
    ], null=True, blank=True)
    
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


class Comorbidity(models.Model):
    """
    Patient comorbidities and medical history
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='comorbidities')
    
    icd10_code = models.CharField(max_length=10)
    condition_name = models.CharField(max_length=255)
    diagnosis_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    severity = models.CharField(max_length=50, null=True, blank=True)
    
    # For calculating comorbidity indices
    charlson_weight = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)


class EMRSyncLog(models.Model):
    """
    Audit trail for EMR data synchronization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sync_logs')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    
    sync_timestamp = models.DateTimeField(auto_now_add=True)
    emr_system = models.CharField(max_length=50)
    sync_type = models.CharField(max_length=50)  # "full", "incremental", "on_demand"
    
    records_synced = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ])
    
    # IRB tracking
    irb_protocol = models.ForeignKey(
        'irb_portal.IRBProtocol', on_delete=models.PROTECT, null=True, blank=True
    )

