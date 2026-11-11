"""
JWT Authentication middleware.
Verifies JWT token from Authorization header and attaches user info to request.
"""
from django.http import JsonResponse
from auth.jwt_utils import verify_token


# Paths that don't require authentication
PUBLIC_PATHS = [
    '/admin/',
    '/auth/register',
    '/auth/login',
    '/auth/refresh',
    '/static/',
    '/media/',
    '/payments/webhook',  # Razorpay webhook (unauthenticated)
]


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default: no user
        request.user_id = None
        request.user_role = None
        request.user_email = None

        # Skip auth for public paths
        path = request.path
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return self.get_response(request)

        # Extract Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            # No token - let the view decide if auth is required
            return self.get_response(request)

        token = auth_header[7:]  # Remove "Bearer "

        try:
            payload = verify_token(token)

            # Reject refresh tokens on regular endpoints
            if payload.get('token_type') != 'access':
                return JsonResponse(
                    {'error': 'Invalid token type. Use access token.'},
                    status=401
                )

            # Attach to request
            request.user_id = payload.get('user_id')
            request.user_role = payload.get('role')
            request.user_email = payload.get('email')

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=401)

        return self.get_response(request)