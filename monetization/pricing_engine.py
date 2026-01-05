"""
Pricing Engine for Data Monetization
Calculates dynamic pricing based on data value and usage
"""
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
from django.db.models import Sum, Count, Avg
from django.db import transaction
from django.utils import timezone

from .models import (
    DataProduct, PricingTier, ProductPricing, DataLicense,
    LicenseUsageLog, RevenueShare, RevenueTransaction, RevenueDistribution
)
from patient_portal.models import PatientAccount, DataAccessGrant
from oncology.models import Patient

logger = logging.getLogger(__name__)


class PricingEngine:
    """
    Calculate pricing for data products based on various factors
    """
    
    # Base pricing factors
    BASE_PRICE_PER_PATIENT = Decimal('5.00')  # Base price per patient record
    
    # Value multipliers by data category
    CATEGORY_MULTIPLIERS = {
        'demographics': Decimal('1.0'),
        'diagnoses': Decimal('1.5'),
        'treatments': Decimal('2.0'),
        'outcomes': Decimal('2.5'),
        'molecular': Decimal('3.0'),
        'genomics': Decimal('4.0'),
        'imaging': Decimal('2.0'),
        'pathology': Decimal('2.5'),
        'biomarkers': Decimal('2.0'),
    }
    
    # Rarity multipliers for cancer types
    RARITY_MULTIPLIERS = {
        'common': Decimal('1.0'),      # >1% incidence
        'uncommon': Decimal('1.5'),    # 0.1-1% incidence
        'rare': Decimal('2.5'),        # <0.1% incidence
        'ultra_rare': Decimal('4.0'),  # <0.01% incidence
    }
    
    # Completeness bonuses
    COMPLETENESS_BONUS = {
        (90, 100): Decimal('1.5'),
        (80, 90): Decimal('1.25'),
        (70, 80): Decimal('1.1'),
        (0, 70): Decimal('1.0'),
    }
    
    @classmethod
    def calculate_product_price(
        cls,
        patient_count: int,
        data_categories: List[str],
        cancer_types: List[str],
        completeness_score: float,
        rarity_level: str = 'common',
        access_level: str = 'deidentified'
    ) -> Dict[str, Decimal]:
        """
        Calculate base price for a data product
        Returns prices for different pricing models
        """
        # Base calculation
        base = cls.BASE_PRICE_PER_PATIENT * patient_count
        
        # Apply category multipliers
        category_factor = Decimal('0')
        for cat in data_categories:
            category_factor += cls.CATEGORY_MULTIPLIERS.get(cat, Decimal('1.0'))
        category_factor = category_factor / len(data_categories) if data_categories else Decimal('1.0')
        
        # Apply rarity multiplier
        rarity_factor = cls.RARITY_MULTIPLIERS.get(rarity_level, Decimal('1.0'))
        
        # Apply completeness bonus
        completeness_factor = Decimal('1.0')
        for (low, high), factor in cls.COMPLETENESS_BONUS.items():
            if low <= completeness_score < high:
                completeness_factor = factor
                break
        
        # Access level adjustments
        access_factors = {
            'aggregate': Decimal('0.3'),
            'deidentified': Decimal('1.0'),
            'limited': Decimal('1.5'),
            'full': Decimal('2.5'),
        }
        access_factor = access_factors.get(access_level, Decimal('1.0'))
        
        # Calculate final base price
        final_base = base * category_factor * rarity_factor * completeness_factor * access_factor
        
        return {
            'one_time': final_base,
            'annual': final_base * Decimal('0.6'),  # 60% for annual subscription
            'per_patient': cls.BASE_PRICE_PER_PATIENT * category_factor * rarity_factor,
            'per_query': Decimal('0.10') * category_factor,  # $0.10 base per query
        }
    
    @classmethod
    def get_tier_pricing(
        cls,
        product: DataProduct,
        tier: PricingTier
    ) -> Dict[str, Decimal]:
        """
        Get pricing for a specific tier
        """
        base_prices = cls.calculate_product_price(
            patient_count=product.patient_count,
            data_categories=product.data_categories,
            cancer_types=product.cancer_types,
            completeness_score=product.completeness_score,
            access_level=product.access_level,
        )
        
        # Apply tier discount
        discount = 1 - (tier.discount_percent / 100)
        
        return {
            model: price * Decimal(str(discount))
            for model, price in base_prices.items()
        }
    
    @classmethod
    def generate_quote(
        cls,
        product: DataProduct,
        tier: PricingTier,
        pricing_model: str,
        duration_months: int = 12,
        estimated_queries: int = 0,
        custom_adjustments: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete pricing quote
        """
        tier_prices = cls.get_tier_pricing(product, tier)
        
        base_price = tier_prices.get(pricing_model, tier_prices['annual'])
        
        # Calculate total based on model
        if pricing_model == 'annual':
            total = base_price * (duration_months / 12)
        elif pricing_model == 'per_query' and estimated_queries:
            total = tier_prices['per_query'] * estimated_queries
        elif pricing_model == 'per_patient':
            total = tier_prices['per_patient'] * product.patient_count
        else:
            total = base_price
        
        # Apply any custom adjustments
        if custom_adjustments:
            if 'discount_percent' in custom_adjustments:
                total *= (1 - custom_adjustments['discount_percent'] / 100)
            if 'volume_discount' in custom_adjustments:
                total *= (1 - custom_adjustments['volume_discount'] / 100)
        
        return {
            'product_id': str(product.id),
            'product_name': product.name,
            'tier_name': tier.name,
            'pricing_model': pricing_model,
            'base_price': base_price,
            'total_price': total,
            'duration_months': duration_months,
            'patient_count': product.patient_count,
            'data_categories': product.data_categories,
            'access_level': product.access_level,
            'quote_valid_until': (datetime.now() + timedelta(days=30)).isoformat(),
        }


class RevenueManager:
    """
    Manages revenue distribution to stakeholders
    """
    
    # Default revenue share percentages
    DEFAULT_SHARES = {
        'platform': Decimal('30.0'),       # HealthDB platform
        'institution': Decimal('40.0'),    # Contributing institutions
        'patient': Decimal('20.0'),        # Patients who contributed data
        'research_fund': Decimal('10.0'),  # Research fund for future studies
    }
    
    @classmethod
    @transaction.atomic
    def process_transaction(
        cls,
        license: DataLicense,
        amount: Decimal,
        transaction_type: str,
        usage_log: LicenseUsageLog = None
    ) -> RevenueTransaction:
        """
        Process a revenue transaction and create distributions
        """
        # Create transaction record
        transaction_obj = RevenueTransaction.objects.create(
            license=license,
            usage_log=usage_log,
            transaction_type=transaction_type,
            amount=amount,
            status='processed',
            processed_at=timezone.now(),
        )
        
        # Get applicable revenue shares
        shares = RevenueShare.objects.filter(
            is_active=True,
        ).filter(
            models.Q(product=license.product) | models.Q(product__isnull=True)
        ).order_by('-share_percent')
        
        # If no custom shares, use defaults
        if not shares.exists():
            shares = cls.DEFAULT_SHARES
            cls._create_distributions_from_defaults(transaction_obj, amount)
        else:
            cls._create_distributions(transaction_obj, shares, amount)
        
        return transaction_obj
    
    @classmethod
    def _create_distributions(
        cls,
        transaction: RevenueTransaction,
        shares: 'QuerySet',
        total_amount: Decimal
    ):
        """
        Create distribution records for each share
        """
        for share in shares:
            share_amount = total_amount * (share.share_percent / 100)
            
            if share.recipient_type == 'patient':
                # Distribute among patients who contributed
                cls._distribute_to_patients(transaction, share, share_amount)
            elif share.recipient_type == 'institution':
                cls._distribute_to_institutions(transaction, share, share_amount)
            else:
                # Platform or research fund
                RevenueDistribution.objects.create(
                    transaction=transaction,
                    revenue_share=share,
                    recipient_type=share.recipient_type,
                    recipient_id=uuid.uuid4(),  # Platform ID
                    amount=share_amount,
                    status='pending',
                )
    
    @classmethod
    def _distribute_to_patients(
        cls,
        transaction: RevenueTransaction,
        share: RevenueShare,
        total_share: Decimal
    ):
        """
        Distribute revenue share to patients
        """
        # Get patients whose data was accessed
        grants = DataAccessGrant.objects.filter(
            access_request__in=transaction.license.product.licenses.values('irb_protocol')
        ).select_related('patient_account')
        
        patient_count = grants.count()
        if patient_count == 0:
            return
        
        per_patient = total_share / patient_count
        
        for grant in grants:
            RevenueDistribution.objects.create(
                transaction=transaction,
                revenue_share=share,
                recipient_type='patient',
                recipient_id=grant.patient_account.id,
                amount=per_patient,
                status='pending',
            )
            
            # Update patient's reward balance
            from patient_portal.services import RewardService
            RewardService.award_points(
                patient_account=grant.patient_account,
                points=int(per_patient * 10),  # $1 = 10 points
                source_type='revenue_share',
                source_id=str(transaction.id),
                description=f'Revenue share from data usage'
            )
    
    @classmethod
    def _distribute_to_institutions(
        cls,
        transaction: RevenueTransaction,
        share: RevenueShare,
        total_share: Decimal
    ):
        """
        Distribute revenue share to contributing institutions
        """
        # Get institutions that contributed data
        patients = Patient.objects.filter(
            portal_account__access_grants__access_request__in=
                transaction.license.product.licenses.values('irb_protocol')
        ).select_related('institution').distinct()
        
        # Count patients per institution
        institution_counts = {}
        for patient in patients:
            inst_id = str(patient.institution.id)
            institution_counts[inst_id] = institution_counts.get(inst_id, 0) + 1
        
        total_patients = sum(institution_counts.values())
        if total_patients == 0:
            return
        
        for inst_id, count in institution_counts.items():
            proportion = Decimal(str(count / total_patients))
            inst_share = total_share * proportion
            
            RevenueDistribution.objects.create(
                transaction=transaction,
                revenue_share=share,
                recipient_type='institution',
                recipient_id=uuid.UUID(inst_id),
                amount=inst_share,
                status='pending',
            )
    
    @classmethod
    def _create_distributions_from_defaults(
        cls,
        transaction: RevenueTransaction,
        total_amount: Decimal
    ):
        """
        Create distributions using default share percentages
        """
        import uuid as uuid_module
        
        for recipient_type, share_percent in cls.DEFAULT_SHARES.items():
            share_amount = total_amount * (share_percent / 100)
            
            RevenueDistribution.objects.create(
                transaction=transaction,
                revenue_share=None,
                recipient_type=recipient_type,
                recipient_id=uuid_module.uuid4(),
                amount=share_amount,
                status='pending',
            )
    
    @classmethod
    def get_revenue_summary(
        cls,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Get summary of revenue and distributions
        """
        transactions = RevenueTransaction.objects.all()
        
        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)
        
        total_revenue = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        distributions = RevenueDistribution.objects.filter(
            transaction__in=transactions
        )
        
        by_recipient = distributions.values('recipient_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        return {
            'total_revenue': total_revenue,
            'transaction_count': transactions.count(),
            'by_transaction_type': dict(
                transactions.values_list('transaction_type').annotate(Sum('amount'))
            ),
            'by_recipient': list(by_recipient),
            'pending_distributions': distributions.filter(status='pending').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0'),
        }


class UsageTracker:
    """
    Track and bill for data usage
    """
    
    @classmethod
    def log_usage(
        cls,
        license: DataLicense,
        user: 'User',
        usage_type: str,
        records_accessed: int,
        data_categories: List[str],
        query_hash: str = None,
        ip_address: str = None
    ) -> LicenseUsageLog:
        """
        Log a usage event and calculate cost
        """
        # Calculate usage cost
        cost = cls._calculate_usage_cost(
            license, usage_type, records_accessed, data_categories
        )
        
        log = LicenseUsageLog.objects.create(
            license=license,
            user=user,
            usage_type=usage_type,
            records_accessed=records_accessed,
            data_categories=data_categories,
            query_hash=query_hash,
            ip_address=ip_address,
            usage_cost=cost,
        )
        
        # Update license usage counts
        license.total_queries += 1 if usage_type == 'query' else 0
        license.total_downloads += 1 if usage_type == 'download' else 0
        license.total_records_accessed += records_accessed
        license.last_accessed = timezone.now()
        license.save()
        
        # Check for overages
        cls._check_overages(license, log)
        
        return log
    
    @classmethod
    def _calculate_usage_cost(
        cls,
        license: DataLicense,
        usage_type: str,
        records_accessed: int,
        data_categories: List[str]
    ) -> Decimal:
        """
        Calculate cost for this usage event
        """
        pricing = license.pricing
        
        if pricing.pricing_model == 'one_time' or pricing.pricing_model == 'annual':
            return Decimal('0')  # Unlimited usage
        
        if pricing.pricing_model == 'per_query' and pricing.price_per_query:
            return pricing.price_per_query
        
        if pricing.pricing_model == 'per_patient' and pricing.price_per_patient:
            return pricing.price_per_patient * records_accessed
        
        return Decimal('0')
    
    @classmethod
    def _check_overages(cls, license: DataLicense, log: LicenseUsageLog):
        """
        Check if usage exceeds limits and create overage charges
        """
        tier = license.pricing.tier
        
        # Check monthly limits
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        monthly_usage = LicenseUsageLog.objects.filter(
            license=license,
            timestamp__gte=month_start
        )
        
        monthly_queries = monthly_usage.filter(usage_type='query').count()
        monthly_exports = monthly_usage.filter(usage_type='export').count()
        
        # Check API call limit
        if tier.max_api_calls_per_month and monthly_queries > tier.max_api_calls_per_month:
            overage_count = monthly_queries - tier.max_api_calls_per_month
            if overage_count == 1:  # First overage this month
                logger.warning(f"License {license.id} exceeded monthly API calls")
        
        # Check export limit
        if tier.max_data_exports_per_month and monthly_exports > tier.max_data_exports_per_month:
            overage_count = monthly_exports - tier.max_data_exports_per_month
            if overage_count == 1:
                logger.warning(f"License {license.id} exceeded monthly exports")
    
    @classmethod
    def get_usage_report(
        cls,
        license: DataLicense,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Generate usage report for a license
        """
        logs = LicenseUsageLog.objects.filter(license=license)
        
        if start_date:
            logs = logs.filter(timestamp__gte=start_date)
        if end_date:
            logs = logs.filter(timestamp__lte=end_date)
        
        return {
            'license_id': str(license.id),
            'period_start': start_date,
            'period_end': end_date,
            'total_queries': logs.filter(usage_type='query').count(),
            'total_downloads': logs.filter(usage_type='download').count(),
            'total_exports': logs.filter(usage_type='export').count(),
            'total_records_accessed': logs.aggregate(Sum('records_accessed'))['records_accessed__sum'] or 0,
            'total_cost': logs.aggregate(Sum('usage_cost'))['usage_cost__sum'] or Decimal('0'),
            'by_category': list(
                logs.values('data_categories').annotate(count=Count('id'))
            ),
            'by_user': list(
                logs.values('user__username').annotate(
                    count=Count('id'),
                    records=Sum('records_accessed')
                )
            ),
        }


# Import uuid for distribution creation
import uuid
from django.db import models

