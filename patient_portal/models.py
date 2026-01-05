"""
Patient Portal Models
Manages patient consent, data access, rewards, and engagement
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from accounts.models import User
from data_collection.models import Institution
from oncology.models import Patient, CancerDiagnosis
import uuid
from datetime import datetime, timedelta


class PatientAccount(models.Model):
    """
    Patient portal account linked to de-identified patient record
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_account')
    
    # Link to de-identified patient record (optional - for verified patients)
    verified_patient = models.OneToOneField(
        Patient, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='portal_account'
    )
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=50, null=True, blank=True)
    # e.g., "emr_link", "document_upload", "institution_verify"
    
    # Self-reported data (before verification)
    self_reported_diagnoses = models.JSONField(default=list)
    self_reported_institution = models.CharField(max_length=255, null=True, blank=True)
    
    # Engagement tracking
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    engagement_level = models.CharField(max_length=20, choices=[
        ('new', 'New'),
        ('active', 'Active'),
        ('engaged', 'Highly Engaged'),
        ('champion', 'Research Champion'),
    ], default='new')
    
    # Preferences
    communication_preferences = models.JSONField(default=dict)
    # e.g., {"email": true, "sms": false, "app_notifications": true}
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)


class ConsentDocument(models.Model):
    """
    Master consent documents for patient data sharing
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    CONSENT_TYPES = [
        ('general_research', 'General Research'),
        ('specific_study', 'Specific Study'),
        ('commercial', 'Commercial Use'),
        ('genetic', 'Genetic/Genomic Research'),
        ('data_sharing', 'External Data Sharing'),
        ('recontact', 'Future Recontact'),
    ]
    
    title = models.CharField(max_length=255)
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPES)
    version = models.CharField(max_length=20)
    
    # Document content
    full_text = models.TextField()
    summary = models.TextField()  # Plain language summary
    key_points = ArrayField(models.CharField(max_length=500), default=list)
    
    # Associated entities
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, null=True, blank=True
    )
    irb_protocol = models.ForeignKey(
        'irb_portal.IRBProtocol', on_delete=models.SET_NULL, null=True, blank=True
    )
    
    # Validity
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Audit
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-effective_date', 'consent_type']


class PatientConsent(models.Model):
    """
    Individual patient consent records
    Immutable audit trail of consent decisions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_account = models.ForeignKey(
        PatientAccount, on_delete=models.PROTECT, related_name='consents'
    )
    consent_document = models.ForeignKey(
        ConsentDocument, on_delete=models.PROTECT
    )
    
    # Consent decision
    is_consented = models.BooleanField()
    consent_date = models.DateTimeField(auto_now_add=True)
    
    # Granular consent options
    consent_options = models.JSONField(default=dict)
    # e.g., {"share_with_pharma": false, "use_for_ai": true, "future_contact": true}
    
    # Withdrawal
    is_withdrawn = models.BooleanField(default=False)
    withdrawal_date = models.DateTimeField(null=True, blank=True)
    withdrawal_reason = models.TextField(null=True, blank=True)
    
    # Verification
    signature_hash = models.CharField(max_length=128)  # Hash of signature
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-consent_date']
        indexes = [
            models.Index(fields=['patient_account', 'consent_document']),
            models.Index(fields=['is_consented', 'is_withdrawn']),
        ]


class DataAccessRequest(models.Model):
    """
    Requests from researchers to access patient data
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Requester
    researcher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='data_access_requests'
    )
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    irb_protocol = models.ForeignKey(
        'irb_portal.IRBProtocol', on_delete=models.PROTECT, null=True, blank=True
    )
    
    # Request details
    title = models.CharField(max_length=255)
    purpose = models.TextField()
    methodology = models.TextField()
    
    # Data requested
    requested_data_types = ArrayField(models.CharField(max_length=50))
    # e.g., ["demographics", "diagnoses", "treatments", "outcomes"]
    
    requested_cancer_types = ArrayField(
        models.CharField(max_length=50), default=list, blank=True
    )
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    
    # Patient criteria
    patient_criteria = models.JSONField(default=dict)
    # e.g., {"age_min": 18, "age_max": 65, "stages": ["III", "IV"]}
    
    estimated_patients = models.IntegerField(null=True, blank=True)
    
    # Access type
    ACCESS_TYPES = [
        ('aggregate', 'Aggregate Statistics Only'),
        ('deidentified', 'De-identified Individual Records'),
        ('limited', 'Limited Dataset'),
        ('identifiable', 'Identifiable Data (with specific consent)'),
    ]
    access_type = models.CharField(max_length=50, choices=ACCESS_TYPES)
    
    # Duration
    access_duration_months = models.IntegerField(default=12)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Review
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_access_requests'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(null=True, blank=True)
    
    # If approved
    access_granted_date = models.DateTimeField(null=True, blank=True)
    access_expires_date = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']


class DataAccessGrant(models.Model):
    """
    Actual access grants connecting requests to patients
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    access_request = models.ForeignKey(
        DataAccessRequest, on_delete=models.CASCADE, related_name='grants'
    )
    patient_account = models.ForeignKey(
        PatientAccount, on_delete=models.CASCADE, related_name='access_grants'
    )
    patient_consent = models.ForeignKey(
        PatientConsent, on_delete=models.PROTECT
    )
    
    # Grant details
    granted_data_types = ArrayField(models.CharField(max_length=50))
    
    # Compensation/rewards
    points_awarded = models.IntegerField(default=0)
    monetary_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    revoked_date = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


class DataAccessLog(models.Model):
    """
    Audit log of all data access events
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    access_grant = models.ForeignKey(
        DataAccessGrant, on_delete=models.CASCADE, related_name='access_logs'
    )
    
    # Access details
    accessed_at = models.DateTimeField(auto_now_add=True)
    accessed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    access_type = models.CharField(max_length=50)  # "view", "download", "query"
    data_categories_accessed = ArrayField(models.CharField(max_length=50))
    records_accessed = models.IntegerField(default=0)
    
    # Technical details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    query_hash = models.CharField(max_length=128, null=True, blank=True)
    
    class Meta:
        ordering = ['-accessed_at']
        indexes = [
            models.Index(fields=['access_grant', 'accessed_at']),
            models.Index(fields=['accessed_by', 'accessed_at']),
        ]


class PatientReward(models.Model):
    """
    Reward/compensation tracking for patient data sharing
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_account = models.ForeignKey(
        PatientAccount, on_delete=models.CASCADE, related_name='rewards'
    )
    
    REWARD_TYPES = [
        ('points', 'Points'),
        ('cash', 'Cash'),
        ('gift_card', 'Gift Card'),
        ('donation', 'Charitable Donation'),
        ('health_credit', 'Health Service Credit'),
    ]
    
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    
    # For points
    points = models.IntegerField(default=0)
    
    # For monetary
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Source
    source_type = models.CharField(max_length=50)  # "data_access", "survey", "referral"
    source_id = models.UUIDField(null=True, blank=True)  # Reference to source object
    description = models.TextField()
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing
    processed_date = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)


class PatientSurvey(models.Model):
    """
    Patient-reported outcome surveys
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Survey structure
    questions = models.JSONField()
    # List of question objects with type, text, options, etc.
    
    # Targeting
    target_cancer_types = ArrayField(
        models.CharField(max_length=50), default=list, blank=True
    )
    target_treatment_types = ArrayField(
        models.CharField(max_length=50), default=list, blank=True
    )
    
    # Timing
    trigger_event = models.CharField(max_length=50, null=True, blank=True)
    # e.g., "post_treatment", "monthly", "diagnosis"
    days_after_trigger = models.IntegerField(null=True, blank=True)
    
    # Rewards
    points_reward = models.IntegerField(default=10)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)


class PatientSurveyResponse(models.Model):
    """
    Patient survey responses
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    survey = models.ForeignKey(
        PatientSurvey, on_delete=models.CASCADE, related_name='responses'
    )
    patient_account = models.ForeignKey(
        PatientAccount, on_delete=models.CASCADE, related_name='survey_responses'
    )
    
    # Response data
    responses = models.JSONField()  # Question ID -> answer mapping
    
    # Metadata
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    
    # Rewards
    points_awarded = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['survey', 'patient_account']


class PatientCommunity(models.Model):
    """
    Patient community groups for specific conditions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Focus
    cancer_types = ArrayField(models.CharField(max_length=50))
    
    # Membership
    members = models.ManyToManyField(
        PatientAccount, through='CommunityMembership', related_name='communities'
    )
    
    # Settings
    is_public = models.BooleanField(default=True)
    requires_verification = models.BooleanField(default=False)
    
    # Moderation
    moderators = models.ManyToManyField(User, related_name='moderated_communities')
    
    created_at = models.DateTimeField(auto_now_add=True)


class CommunityMembership(models.Model):
    """
    Patient community membership
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    community = models.ForeignKey(PatientCommunity, on_delete=models.CASCADE)
    patient_account = models.ForeignKey(PatientAccount, on_delete=models.CASCADE)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20, default='member')
    # "member", "contributor", "moderator"
    
    class Meta:
        unique_together = ['community', 'patient_account']


class PatientNotification(models.Model):
    """
    Notifications for patients
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_account = models.ForeignKey(
        PatientAccount, on_delete=models.CASCADE, related_name='notifications'
    )
    
    NOTIFICATION_TYPES = [
        ('survey_available', 'New Survey Available'),
        ('data_accessed', 'Your Data Was Accessed'),
        ('reward_earned', 'Reward Earned'),
        ('consent_expiring', 'Consent Expiring Soon'),
        ('study_invitation', 'Study Invitation'),
        ('community_update', 'Community Update'),
        ('system', 'System Notification'),
    ]
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Action
    action_url = models.URLField(null=True, blank=True)
    action_text = models.CharField(max_length=100, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

