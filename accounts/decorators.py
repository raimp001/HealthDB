from django.http import HttpResponseForbidden
from functools import wraps

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("Insufficient permissions")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def permission_required(perm):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(perm):
                return HttpResponseForbidden("Permission denied")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 