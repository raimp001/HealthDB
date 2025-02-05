from django.db import transaction
from .models import IRBProtocol, ProtocolVersion, CollaborationThread

class IRBWorkflowEngine:
    def create_protocol(self, user, title, document):
        """Create new protocol draft with version history"""
        with transaction.atomic():
            protocol = IRBProtocol.objects.create(
                title=title,
                institution=user.institution,
                lead_investigator=user,
                document=document
            )
            self._create_initial_version(protocol, document)
            return protocol
    
    def submit_for_review(self, protocol):
        """Transition protocol to under review state"""
        protocol.status = 'under_review'
        protocol.save()
        self._notify_reviewers(protocol)
    
    def create_review_thread(self, protocol, user, section):
        """Start new collaboration thread for specific protocol section"""
        thread = CollaborationThread.objects.create(protocol=protocol)
        thread.participants.add(user)
        return thread
    
    def add_protocol_version(self, protocol, user, document, changes):
        """Create new protocol version with change tracking"""
        new_version = ProtocolVersion.objects.create(
            protocol=protocol,
            version_number=protocol.version + 1,
            document=document,
            change_description=changes
        )
        protocol.version = new_version.version_number
        protocol.save()
        return new_version
    
    def _create_initial_version(self, protocol, document):
        ProtocolVersion.objects.create(
            protocol=protocol,
            version_number=1,
            document=document,
            change_description="Initial protocol version"
        )
    
    def _notify_reviewers(self, protocol):
        # Implement institution-specific notification logic
        pass 