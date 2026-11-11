"""
JWT token generation and verification.
Uses HS256 with Django's SECRET_KEY.
"""
import jwt
from datetime import datetime, timezone
from django.conf import settings


def generate_access_token(user_id: str, role: str, email: str) -> str:
    """Generate a short-lived access token (60 min)."""
    now = datetime.now(timezone.utc)
    payload = {
        'user_id': str(user_id),
        'role': role,
        'email': email,
        'token_type': 'access',
        'iat': now,
        'exp': now + settings.JWT_ACCESS_TOKEN_LIFETIME,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def generate_refresh_token(user_id: str) -> str:
    """Generate a long-lived refresh token (7 days)."""
    now = datetime.now(timezone.utc)
    payload = {
        'user_id': str(user_id),
        'token_type': 'refresh',
        'iat': now,
        'exp': now + settings.JWT_REFRESH_TOKEN_LIFETIME,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    Returns decoded payload or raises exception.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')


def generate_token_pair(user_id: str, role: str, email: str) -> dict:
    """Generate both access and refresh tokens."""
    return {
        'access_token': generate_access_token(user_id, role, email),
        'refresh_token': generate_refresh_token(user_id),
        'token_type': 'Bearer',
        'expires_in': int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
    }