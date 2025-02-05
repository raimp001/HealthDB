from django.db import models

class IRBProtocol(models.Model):
    PROTOCOL_STATUS = (
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('revisions', 'Needs Revisions'),
    )
    
    title = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE)
    lead_investigator = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=PROTOCOL_STATUS, default='draft')
    document = models.FileField(upload_to='irb_protocols/')  # Store in encrypted storage
    approval_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

class ProtocolVersion(models.Model):
    protocol = models.ForeignKey(IRBProtocol, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    change_description = models.TextField()
    document = models.FileField(upload_to='irb_versions/')
    created_at = models.DateTimeField(auto_now_add=True)

class CollaborationThread(models.Model):
    protocol = models.ForeignKey(IRBProtocol, on_delete=models.CASCADE, related_name='threads')
    participants = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

class ProtocolComment(models.Model):
    thread = models.ForeignKey(CollaborationThread, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reference_section = models.CharField(max_length=100)  # Section of protocol being discussed 