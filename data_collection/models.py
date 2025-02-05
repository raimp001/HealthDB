from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class DeIdentificationLog(models.Model):
    """Audit trail for data de-identification process"""
    original_hash = models.CharField(max_length=128)
    deidentified_hash = models.CharField(max_length=128)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class LongitudinalData(models.Model):
    """Core model for storing longitudinal rare disease data"""
    PATIENT_ID_SALT = "your-secure-salt"  # Store in secure vault
    
    hashed_patient_id = models.CharField(max_length=128)  # SHA-256 of (ID + salt)
    disease = models.ForeignKey('DiseaseRegistry', on_delete=models.CASCADE)
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE)
    collection_date = models.DateField()
    time_since_diagnosis = models.IntegerField()  # In months
    data_points = models.JSONField()  # Structured data points
    irb_protocol = models.ForeignKey('irb_portal.IRBProtocol', on_delete=models.PROTECT)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hashed_patient_id', 'collection_date'],
                name='unique_patient_data_point'
            )
        ]

class DiseaseRegistry(models.Model):
    """Curated list of rare diseases with data collection templates"""
    icd_code = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    data_template = models.JSONField()  # JSON Schema for validation
    version = models.PositiveIntegerField(default=1)
    effective_date = models.DateField()

class Institution(models.Model):
    """Participating healthcare institutions"""
    name = models.CharField(max_length=255)
    irb_contact = models.EmailField()
    partnership_date = models.DateField()
    is_active = models.BooleanField(default=True) 