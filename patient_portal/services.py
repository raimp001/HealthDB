"""
Patient Portal Services
Business logic for patient consent, data sharing, and rewards
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
import hashlib
import logging

from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import (
    PatientAccount, ConsentDocument, PatientConsent,
    DataAccessRequest, DataAccessGrant, DataAccessLog,
    PatientReward, PatientSurvey, PatientSurveyResponse,
    PatientNotification
)
from oncology.models import Patient, CancerDiagnosis
from accounts.models import User

logger = logging.getLogger(__name__)


class ConsentService:
    """
    Manages patient consent workflows
    """
    
    @staticmethod
    @transaction.atomic
    def record_consent(
        patient_account: PatientAccount,
        consent_document: ConsentDocument,
        is_consented: bool,
        consent_options: Dict[str, Any],
        signature: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> PatientConsent:
        """
        Record a patient's consent decision
        Creates an immutable audit record
        """
        # Hash the signature for storage
        signature_hash = hashlib.sha256(signature.encode()).hexdigest()
        
        # Calculate expiration if applicable
        expires_at = None
        if consent_document.expiration_date:
            expires_at = datetime.combine(
                consent_document.expiration_date,
                datetime.min.time()
            )
        
        consent = PatientConsent.objects.create(
            patient_account=patient_account,
            consent_document=consent_document,
            is_consented=is_consented,
            consent_options=consent_options,
            signature_hash=signature_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        
        # Update patient's data sharing level if this is a general consent
        if is_consented and consent_document.consent_type == 'general_research':
            ConsentService._update_patient_sharing_level(patient_account)
        
        # Award points for completing consent
        RewardService.award_points(
            patient_account=patient_account,
            points=25,
            source_type='consent',
            source_id=consent.id,
            description=f"Completed consent for {consent_document.title}"
        )
        
        return consent
    
    @staticmethod
    @transaction.atomic
    def withdraw_consent(
        consent_id: str,
        reason: str = None
    ) -> PatientConsent:
        """
        Withdraw a previously given consent
        """
        consent = PatientConsent.objects.get(id=consent_id)
        
        if consent.is_withdrawn:
            raise ValueError("This consent has already been withdrawn")
        
        consent.is_withdrawn = True
        consent.withdrawal_date = timezone.now()
        consent.withdrawal_reason = reason
        consent.save()
        
        # Revoke any active data access grants based on this consent
        DataAccessGrant.objects.filter(
            patient_consent=consent,
            is_active=True
        ).update(
            is_active=False,
            revoked_date=timezone.now(),
            revocation_reason="Patient withdrew consent"
        )
        
        # Send notification
        NotificationService.send_notification(
            patient_account=consent.patient_account,
            notification_type='system',
            title='Consent Withdrawn',
            message=f'Your consent for "{consent.consent_document.title}" has been withdrawn.'
        )
        
        return consent
    
    @staticmethod
    def get_active_consents(patient_account: PatientAccount) -> List[PatientConsent]:
        """
        Get all active (non-withdrawn, non-expired) consents for a patient
        """
        now = timezone.now()
        return PatientConsent.objects.filter(
            patient_account=patient_account,
            is_consented=True,
            is_withdrawn=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).select_related('consent_document')
    
    @staticmethod
    def check_consent_for_access(
        patient_account: PatientAccount,
        access_type: str,
        data_categories: List[str]
    ) -> Dict[str, bool]:
        """
        Check if patient has consented to specific data access
        Returns dict of category -> consented boolean
        """
        active_consents = ConsentService.get_active_consents(patient_account)
        
        result = {cat: False for cat in data_categories}
        
        for consent in active_consents:
            options = consent.consent_options
            doc_type = consent.consent_document.consent_type
            
            # General research consent covers most categories
            if doc_type == 'general_research':
                for cat in data_categories:
                    if cat not in ['genetic', 'identifiable']:
                        result[cat] = True
            
            # Specific consent types
            if doc_type == 'genetic' and 'genetic' in data_categories:
                result['genetic'] = True
            
            if doc_type == 'commercial':
                # Check specific options for commercial use
                if options.get('share_with_pharma', False):
                    for cat in data_categories:
                        result[cat] = True
        
        return result
    
    @staticmethod
    def _update_patient_sharing_level(patient_account: PatientAccount):
        """
        Update patient's overall data sharing level based on consents
        """
        active_consents = ConsentService.get_active_consents(patient_account)
        
        if not active_consents:
            level = 'none'
        elif any(c.consent_document.consent_type == 'commercial' for c in active_consents):
            level = 'full'
        elif any(c.consent_document.consent_type == 'general_research' for c in active_consents):
            level = 'research_only'
        else:
            level = 'none'
        
        if patient_account.verified_patient:
            patient_account.verified_patient.data_sharing_level = level
            patient_account.verified_patient.save()


class DataAccessService:
    """
    Manages researcher data access requests and grants
    """
    
    @staticmethod
    @transaction.atomic
    def submit_request(
        researcher: User,
        title: str,
        purpose: str,
        methodology: str,
        requested_data_types: List[str],
        access_type: str,
        patient_criteria: Dict[str, Any] = None,
        irb_protocol_id: str = None,
        **kwargs
    ) -> DataAccessRequest:
        """
        Submit a new data access request
        """
        request = DataAccessRequest.objects.create(
            researcher=researcher,
            institution=researcher.institution,
            title=title,
            purpose=purpose,
            methodology=methodology,
            requested_data_types=requested_data_types,
            access_type=access_type,
            patient_criteria=patient_criteria or {},
            irb_protocol_id=irb_protocol_id,
            status='submitted',
            **kwargs
        )
        
        # Estimate number of patients matching criteria
        request.estimated_patients = DataAccessService._estimate_patient_count(
            patient_criteria or {},
            kwargs.get('requested_cancer_types', [])
        )
        request.save()
        
        return request
    
    @staticmethod
    @transaction.atomic
    def approve_request(
        request_id: str,
        reviewer: User,
        notes: str = None
    ) -> DataAccessRequest:
        """
        Approve a data access request
        """
        request = DataAccessRequest.objects.get(id=request_id)
        
        if request.status != 'under_review':
            raise ValueError(f"Cannot approve request in status: {request.status}")
        
        request.status = 'approved'
        request.reviewed_by = reviewer
        request.review_date = timezone.now()
        request.review_notes = notes
        request.access_granted_date = timezone.now()
        request.access_expires_date = timezone.now() + timedelta(
            days=request.access_duration_months * 30
        )
        request.save()
        
        # Create access grants for eligible patients
        DataAccessService._create_access_grants(request)
        
        return request
    
    @staticmethod
    def _create_access_grants(request: DataAccessRequest) -> int:
        """
        Create access grants for patients matching request criteria
        Returns number of grants created
        """
        # Find patients with active consents matching the request
        eligible_accounts = PatientAccount.objects.filter(
            verified_patient__isnull=False,
            verified_patient__data_sharing_level__in=['research_only', 'full']
        )
        
        # Apply cancer type filter if specified
        if request.requested_cancer_types:
            eligible_accounts = eligible_accounts.filter(
                verified_patient__diagnoses__cancer_type__name__in=request.requested_cancer_types
            ).distinct()
        
        # Apply patient criteria filters
        criteria = request.patient_criteria
        if criteria:
            if 'age_min' in criteria:
                current_year = datetime.now().year
                eligible_accounts = eligible_accounts.filter(
                    verified_patient__birth_year__lte=current_year - criteria['age_min']
                )
            if 'age_max' in criteria:
                current_year = datetime.now().year
                eligible_accounts = eligible_accounts.filter(
                    verified_patient__birth_year__gte=current_year - criteria['age_max']
                )
        
        grants_created = 0
        
        for account in eligible_accounts:
            # Check consent for requested data types
            consent_check = ConsentService.check_consent_for_access(
                account,
                request.access_type,
                request.requested_data_types
            )
            
            # Only grant access to consented categories
            granted_types = [cat for cat, consented in consent_check.items() if consented]
            
            if granted_types:
                # Find the most recent applicable consent
                consent = ConsentService.get_active_consents(account).first()
                
                if consent:
                    grant = DataAccessGrant.objects.create(
                        access_request=request,
                        patient_account=account,
                        patient_consent=consent,
                        granted_data_types=granted_types,
                    )
                    
                    # Award points to patient
                    RewardService.award_points(
                        patient_account=account,
                        points=50,
                        source_type='data_access',
                        source_id=grant.id,
                        description=f"Your data is contributing to research: {request.title}"
                    )
                    
                    # Notify patient
                    NotificationService.send_notification(
                        patient_account=account,
                        notification_type='data_accessed',
                        title='Your Data is Helping Research',
                        message=f'A researcher has been granted access to your data for: {request.title}'
                    )
                    
                    grants_created += 1
        
        return grants_created
    
    @staticmethod
    def log_access(
        grant: DataAccessGrant,
        user: User,
        access_type: str,
        data_categories: List[str],
        records_count: int,
        ip_address: str = None,
        query_hash: str = None
    ) -> DataAccessLog:
        """
        Log a data access event for audit purposes
        """
        return DataAccessLog.objects.create(
            access_grant=grant,
            accessed_by=user,
            access_type=access_type,
            data_categories_accessed=data_categories,
            records_accessed=records_count,
            ip_address=ip_address,
            query_hash=query_hash,
        )
    
    @staticmethod
    def _estimate_patient_count(
        criteria: Dict[str, Any],
        cancer_types: List[str]
    ) -> int:
        """
        Estimate the number of patients matching criteria
        """
        query = Patient.objects.filter(data_sharing_level__in=['research_only', 'full'])
        
        if cancer_types:
            query = query.filter(
                diagnoses__cancer_type__name__in=cancer_types
            ).distinct()
        
        if criteria.get('age_min'):
            current_year = datetime.now().year
            query = query.filter(birth_year__lte=current_year - criteria['age_min'])
        
        if criteria.get('age_max'):
            current_year = datetime.now().year
            query = query.filter(birth_year__gte=current_year - criteria['age_max'])
        
        return query.count()


class RewardService:
    """
    Manages patient rewards and compensation
    """
    
    # Points to USD conversion rate
    POINTS_TO_USD = Decimal('0.01')  # 100 points = $1
    
    @staticmethod
    @transaction.atomic
    def award_points(
        patient_account: PatientAccount,
        points: int,
        source_type: str,
        source_id: str,
        description: str
    ) -> PatientReward:
        """
        Award points to a patient
        """
        reward = PatientReward.objects.create(
            patient_account=patient_account,
            reward_type='points',
            points=points,
            source_type=source_type,
            source_id=source_id,
            description=description,
            status='processed',
            processed_date=timezone.now(),
        )
        
        # Update account totals
        patient_account.points_earned += points
        patient_account.save()
        
        # Check for engagement level upgrades
        RewardService._check_engagement_level(patient_account)
        
        return reward
    
    @staticmethod
    @transaction.atomic
    def redeem_points(
        patient_account: PatientAccount,
        points: int,
        redemption_type: str,  # 'cash', 'gift_card', 'donation'
        details: Dict[str, Any] = None
    ) -> PatientReward:
        """
        Redeem points for rewards
        """
        available_points = patient_account.points_earned - patient_account.points_redeemed
        
        if points > available_points:
            raise ValueError(f"Insufficient points. Available: {available_points}")
        
        amount = Decimal(points) * RewardService.POINTS_TO_USD
        
        reward = PatientReward.objects.create(
            patient_account=patient_account,
            reward_type=redemption_type,
            points=-points,  # Negative for redemption
            amount=amount,
            source_type='redemption',
            description=f"Redeemed {points} points for {redemption_type}",
            status='pending',
        )
        
        # Update account totals
        patient_account.points_redeemed += points
        patient_account.save()
        
        return reward
    
    @staticmethod
    def get_patient_rewards_summary(patient_account: PatientAccount) -> Dict[str, Any]:
        """
        Get summary of patient's rewards
        """
        rewards = PatientReward.objects.filter(patient_account=patient_account)
        
        return {
            'total_points_earned': patient_account.points_earned,
            'points_redeemed': patient_account.points_redeemed,
            'available_points': patient_account.points_earned - patient_account.points_redeemed,
            'cash_value': Decimal(
                patient_account.points_earned - patient_account.points_redeemed
            ) * RewardService.POINTS_TO_USD,
            'rewards_by_source': rewards.values('source_type').annotate(
                total=Sum('points'),
                count=Count('id')
            ),
            'engagement_level': patient_account.engagement_level,
        }
    
    @staticmethod
    def _check_engagement_level(patient_account: PatientAccount):
        """
        Check and update patient engagement level based on activity
        """
        points = patient_account.points_earned
        
        if points >= 1000:
            level = 'champion'
        elif points >= 500:
            level = 'engaged'
        elif points >= 100:
            level = 'active'
        else:
            level = 'new'
        
        if level != patient_account.engagement_level:
            patient_account.engagement_level = level
            patient_account.save()
            
            # Send congratulations notification
            NotificationService.send_notification(
                patient_account=patient_account,
                notification_type='reward_earned',
                title=f'Congratulations! You are now a {level.title()} member!',
                message=f'Thank you for your continued contribution to research.'
            )


class NotificationService:
    """
    Manages patient notifications
    """
    
    @staticmethod
    def send_notification(
        patient_account: PatientAccount,
        notification_type: str,
        title: str,
        message: str,
        action_url: str = None,
        action_text: str = None
    ) -> PatientNotification:
        """
        Send a notification to a patient
        """
        notification = PatientNotification.objects.create(
            patient_account=patient_account,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            action_text=action_text,
        )
        
        # TODO: Send push notification / email based on preferences
        prefs = patient_account.communication_preferences
        
        if prefs.get('email', True):
            # Send email notification
            pass
        
        if prefs.get('sms', False):
            # Send SMS notification
            pass
        
        return notification
    
    @staticmethod
    def get_unread_count(patient_account: PatientAccount) -> int:
        """
        Get count of unread notifications
        """
        return PatientNotification.objects.filter(
            patient_account=patient_account,
            is_read=False
        ).count()
    
    @staticmethod
    def mark_as_read(notification_id: str) -> PatientNotification:
        """
        Mark a notification as read
        """
        notification = PatientNotification.objects.get(id=notification_id)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return notification


class PatientVerificationService:
    """
    Manages patient identity verification
    """
    
    @staticmethod
    @transaction.atomic
    def initiate_emr_verification(
        patient_account: PatientAccount,
        institution: 'Institution',
        mrn: str
    ) -> Dict[str, Any]:
        """
        Initiate verification by linking to EMR record
        """
        from emr_connectors.base import ConnectionConfig, EMRType
        from data_collection.deidentification import DeIdentifier
        
        # This would trigger an out-of-band verification
        # (e.g., send verification code to patient's email on file in EMR)
        
        return {
            'status': 'pending',
            'verification_id': str(patient_account.id),
            'next_step': 'check_email',
            'message': 'Please check your email registered with the hospital for a verification code.'
        }
    
    @staticmethod
    @transaction.atomic
    def complete_verification(
        patient_account: PatientAccount,
        verification_code: str,
        hashed_mrn: str
    ) -> bool:
        """
        Complete the verification process
        """
        # In production, verify the code and link accounts
        
        # Find or create de-identified patient record
        patient, created = Patient.objects.get_or_create(
            hashed_mrn=hashed_mrn,
            defaults={
                'institution': patient_account.user.institution,
            }
        )
        
        patient_account.verified_patient = patient
        patient_account.is_verified = True
        patient_account.verification_date = timezone.now()
        patient_account.verification_method = 'emr_link'
        patient_account.save()
        
        # Award points for verification
        RewardService.award_points(
            patient_account=patient_account,
            points=100,
            source_type='verification',
            source_id=patient_account.id,
            description='Completed identity verification'
        )
        
        return True

