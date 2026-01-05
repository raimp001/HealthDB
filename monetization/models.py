"""
Data Monetization Models
Manages pricing, licensing, and revenue distribution for healthcare data
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from data_collection.models import Institution
from patient_portal.models import DataAccessRequest
import uuid
from decimal import Decimal


class DataProduct(models.Model):
    """
    Packaged data products available for licensing
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Product details
    name = models.CharField(max_length=255)
    description = models.TextField()
    short_description = models.CharField(max_length=500)
    
    PRODUCT_TYPES = [
        ('dataset', 'Complete Dataset'),
        ('cohort', 'Pre-built Cohort'),
        ('analytics', 'Analytics Report'),
        ('api_access', 'API Access'),
        ('custom', 'Custom Data Extract'),
    ]
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPES)
    
    # Data characteristics
    cancer_types = ArrayField(models.CharField(max_length=100), default=list)
    data_categories = ArrayField(models.CharField(max_length=50), default=list)
    # e.g., ["demographics", "diagnoses", "treatments", "outcomes", "molecular"]
    
    patient_count = models.IntegerField()
    record_count = models.IntegerField()
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    
    # Data quality indicators
    completeness_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    data_dictionary_url = models.URLField(null=True, blank=True)
    sample_data_url = models.URLField(null=True, blank=True)
    
    # Access levels
    ACCESS_LEVELS = [
        ('aggregate', 'Aggregate Statistics Only'),
        ('deidentified', 'De-identified Individual Records'),
        ('limited', 'Limited Dataset (Dates, ZIP)'),
        ('full', 'Full Research Dataset'),
    ]
    access_level = models.CharField(max_length=50, choices=ACCESS_LEVELS)
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Tracking
    view_count = models.IntegerField(default=0)
    inquiry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']


class PricingTier(models.Model):
    """
    Pricing tiers for data products
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    TIER_TYPES = [
        ('academic', 'Academic/Non-profit'),
        ('startup', 'Startup/Small Business'),
        ('enterprise', 'Enterprise'),
        ('pharma', 'Pharmaceutical'),
        ('government', 'Government'),
    ]
    tier_type = models.CharField(max_length=50, choices=TIER_TYPES)
    
    # Discount percentage from base price
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    
    # Verification requirements
    requires_verification = models.BooleanField(default=True)
    verification_documents = ArrayField(
        models.CharField(max_length=100), default=list
    )
    # e.g., ["nonprofit_status", "academic_affiliation", "irb_approval"]
    
    # Usage limits
    max_api_calls_per_month = models.IntegerField(null=True, blank=True)
    max_data_exports_per_month = models.IntegerField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['discount_percent']


class ProductPricing(models.Model):
    """
    Pricing for data products per tier
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    product = models.ForeignKey(
        DataProduct, on_delete=models.CASCADE, related_name='pricing'
    )
    tier = models.ForeignKey(
        PricingTier, on_delete=models.CASCADE, related_name='product_prices'
    )
    
    # Pricing model
    PRICING_MODELS = [
        ('one_time', 'One-time License'),
        ('annual', 'Annual Subscription'),
        ('per_query', 'Per Query'),
        ('per_patient', 'Per Patient Record'),
        ('per_download', 'Per Download'),
        ('custom', 'Custom Quote'),
    ]
    pricing_model = models.CharField(max_length=50, choices=PRICING_MODELS)
    
    # Base price (before tier discount)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Variable pricing
    price_per_patient = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    price_per_query = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    minimum_commitment = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    
    # Duration
    license_duration_months = models.IntegerField(default=12)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['product', 'tier', 'pricing_model']
    
    @property
    def final_price(self) -> Decimal:
        """Calculate final price after tier discount"""
        discount = self.tier.discount_percent / 100
        return self.base_price * (1 - discount)


class DataLicense(models.Model):
    """
    Actual data licenses purchased by customers
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Licensee
    licensee = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='data_licenses'
    )
    institution = models.ForeignKey(
        Institution, on_delete=models.PROTECT, related_name='data_licenses'
    )
    
    # Product and pricing
    product = models.ForeignKey(
        DataProduct, on_delete=models.PROTECT, related_name='licenses'
    )
    pricing = models.ForeignKey(
        ProductPricing, on_delete=models.PROTECT
    )
    
    # Custom pricing (for negotiated deals)
    negotiated_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    price_justification = models.TextField(null=True, blank=True)
    
    # License terms
    LICENSE_STATUS = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]
    status = models.CharField(max_length=20, choices=LICENSE_STATUS, default='pending')
    
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renew = models.BooleanField(default=False)
    
    # Legal
    contract_document = models.FileField(
        upload_to='licenses/contracts/', null=True, blank=True
    )
    signed_date = models.DateField(null=True, blank=True)
    signed_by = models.CharField(max_length=255, null=True, blank=True)
    
    # Usage tracking
    total_queries = models.IntegerField(default=0)
    total_downloads = models.IntegerField(default=0)
    total_records_accessed = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # IRB linkage
    irb_protocol = models.ForeignKey(
        'irb_portal.IRBProtocol', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def final_amount(self) -> Decimal:
        """Get the final amount for this license"""
        if self.negotiated_price:
            return self.negotiated_price
        return self.pricing.final_price


class LicenseUsageLog(models.Model):
    """
    Detailed usage tracking for licenses
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    license = models.ForeignKey(
        DataLicense, on_delete=models.CASCADE, related_name='usage_logs'
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Usage details
    USAGE_TYPES = [
        ('query', 'Data Query'),
        ('download', 'Data Download'),
        ('api_call', 'API Call'),
        ('view', 'Data View'),
        ('export', 'Data Export'),
    ]
    usage_type = models.CharField(max_length=50, choices=USAGE_TYPES)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    records_accessed = models.IntegerField(default=0)
    data_categories = ArrayField(models.CharField(max_length=50), default=list)
    
    # Query details (hashed for audit)
    query_hash = models.CharField(max_length=128, null=True, blank=True)
    query_duration_ms = models.IntegerField(null=True, blank=True)
    
    # Technical details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Cost calculation
    usage_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['license', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]


class RevenueShare(models.Model):
    """
    Revenue sharing configuration for data contributors
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Revenue share recipients
    RECIPIENT_TYPES = [
        ('patient', 'Patient'),
        ('institution', 'Contributing Institution'),
        ('platform', 'Platform (HealthDB)'),
        ('research_fund', 'Research Fund'),
    ]
    recipient_type = models.CharField(max_length=50, choices=RECIPIENT_TYPES)
    
    # Share percentage
    share_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Conditions
    product = models.ForeignKey(
        DataProduct, on_delete=models.CASCADE,
        null=True, blank=True, related_name='revenue_shares'
    )
    # If null, applies to all products
    
    # For patient shares
    patient_min_contribution = models.IntegerField(default=0)
    # Minimum data points required to receive share
    
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()
    
    class Meta:
        ordering = ['recipient_type', '-share_percent']


class RevenueTransaction(models.Model):
    """
    Individual revenue transactions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Source
    license = models.ForeignKey(
        DataLicense, on_delete=models.PROTECT, related_name='revenue_transactions'
    )
    usage_log = models.ForeignKey(
        LicenseUsageLog, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    # Transaction details
    TRANSACTION_TYPES = [
        ('license_fee', 'License Fee'),
        ('usage_fee', 'Usage Fee'),
        ('renewal', 'Renewal'),
        ('overage', 'Overage Charge'),
    ]
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('distributed', 'Distributed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment reference
    payment_processor = models.CharField(max_length=50, null=True, blank=True)
    payment_reference = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)


class RevenueDistribution(models.Model):
    """
    Distribution of revenue to stakeholders
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    transaction = models.ForeignKey(
        RevenueTransaction, on_delete=models.CASCADE,
        related_name='distributions'
    )
    revenue_share = models.ForeignKey(
        RevenueShare, on_delete=models.PROTECT
    )
    
    # Recipient details
    recipient_type = models.CharField(max_length=50)
    recipient_id = models.UUIDField()  # ID of patient, institution, etc.
    
    # Amount
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment details
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    payment_reference = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)


class DataMarketplaceListing(models.Model):
    """
    Marketplace listings for data discovery
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    product = models.OneToOneField(
        DataProduct, on_delete=models.CASCADE, related_name='listing'
    )
    
    # Display
    headline = models.CharField(max_length=200)
    tags = ArrayField(models.CharField(max_length=50), default=list)
    thumbnail_url = models.URLField(null=True, blank=True)
    
    # SEO
    slug = models.SlugField(max_length=255, unique=True)
    meta_description = models.CharField(max_length=300, null=True, blank=True)
    
    # Ranking
    relevance_score = models.FloatField(default=0)
    popularity_score = models.FloatField(default=0)
    
    # Publication
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    conversion_rate = models.FloatField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DataInquiry(models.Model):
    """
    Inquiries from potential customers
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Inquirer
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    email = models.EmailField()
    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    role = models.CharField(max_length=100, null=True, blank=True)
    
    # Inquiry details
    product = models.ForeignKey(
        DataProduct, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='inquiries'
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    # Requested info
    interested_in = ArrayField(models.CharField(max_length=100), default=list)
    # e.g., ["pricing", "data_sample", "custom_cohort", "api_access"]
    
    budget_range = models.CharField(max_length=50, null=True, blank=True)
    timeline = models.CharField(max_length=100, null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('proposal_sent', 'Proposal Sent'),
        ('negotiating', 'Negotiating'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_inquiries'
    )
    
    # Follow-up
    notes = models.TextField(null=True, blank=True)
    next_follow_up = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Data inquiries'

