from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLES = (
        ('ADMIN', 'System Administrator'),
        ('IRB', 'IRB Committee Member'),
        ('RESEARCHER', 'Principal Investigator'),
        ('DATA_CURATOR', 'Data Curator'),
        ('INST_ADMIN', 'Institution Administrator'),
    )
    
    role = models.CharField(max_length=20, choices=ROLES, default='RESEARCHER')
    institution = models.ForeignKey('data_collection.Institution', on_delete=models.CASCADE, null=True)
    two_factor_enabled = models.BooleanField(default=False)
    last_access = models.DateTimeField(null=True)
    
    class Meta:
        permissions = [
            ("submit_irb_protocol", "Can submit IRB protocols"),
            ("review_irb_protocol", "Can review IRB protocols"),
            ("upload_data", "Can upload research data"),
            ("curate_data", "Can curate and validate data"),
            ("manage_institution", "Can manage institution settings"),
        ] 