from django.http import HttpResponseForbidden
from django.urls import reverse

class AccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip authentication for admin URLs
        if request.path.startswith(reverse('admin:index')):
            return None
            
        # Check institution status
        if hasattr(request.user, 'institution') and request.user.institution:
            if not request.user.institution.is_active:
                return HttpResponseForbidden("Institution account suspended")
        
        return None 