"""
Role-based access control guards.
Use as decorators on view functions.
"""
from functools import wraps
from django.http import JsonResponse


def require_auth(view_func):
    """Decorator: require any authenticated user."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user_id:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(*allowed_roles):
    """
    Decorator: require user to have one of the specified roles.
    Usage: @require_role('admin') or @require_role('customer', 'admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user_id:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            if request.user_role not in allowed_roles:
                return JsonResponse(
                    {'error': f'Access denied. Required role: {", ".join(allowed_roles)}'},
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def caller_entity(request) -> dict:
    """Get current authenticated user info from request."""
    return {
        'user_id': request.user_id,
        'role': request.user_role,
        'email': request.user_email,
    }


# Role-specific shortcuts
require_customer = require_role('customer')
require_restaurant_owner = require_role('restaurant_owner')
require_delivery_partner = require_role('delivery_partner')
require_admin = require_role('admin')