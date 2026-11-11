"""
Authentication endpoints: register, login, refresh, me, logout.
"""
import json
import re
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods






from django.urls import path
from django.db import connection, IntegrityError

from auth.password_utils import hash_password, verify_password
from auth.jwt_utils import generate_token_pair, verify_token, generate_access_token
from auth.guards import require_auth, caller_entity
from core.Cache.cache_invalidation import invalidate_user_profile


VALID_ROLES = {'customer', 'restaurant_owner', 'delivery_partner', 'admin'}
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^\+?[0-9]{10,15}$')


# ============================================================================
# POST /auth/register
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    """Register a new user."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    role = data.get('role', '').strip().lower()

    if not name or len(name) < 2:
        return JsonResponse({'error': 'Name is required (min 2 chars)'}, status=400)
    if not EMAIL_REGEX.match(email):
        return JsonResponse({'error': 'Invalid email format'}, status=400)
    if not PHONE_REGEX.match(phone):
        return JsonResponse({'error': 'Invalid phone number'}, status=400)
    if len(password) < 8:
        return JsonResponse({'error': 'Password must be at least 8 characters'}, status=400)
    if role not in VALID_ROLES:
        return JsonResponse(
            {'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'},
            status=400
        )

    password_hash = hash_password(password)
    user_id = str(uuid.uuid4())

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (id, name, email, password_hash, phone, role, is_active, is_available)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [user_id, name, email, password_hash, phone, role, True, False])
    except IntegrityError as e:
        error_msg = str(e).lower()
        if 'email' in error_msg:
            return JsonResponse({'error': 'Email already registered'}, status=409)
        if 'phone' in error_msg:
            return JsonResponse({'error': 'Phone already registered'}, status=409)
        return JsonResponse({'error': 'User already exists'}, status=409)
    except Exception as e:
        return JsonResponse({'error': f'Registration failed: {str(e)}'}, status=500)

    tokens = generate_token_pair(user_id, role, email)

    # Send welcome email asynchronously
    try:
        from core.Tasks.order_tasks import send_welcome_email_async
        send_welcome_email_async.delay(user_id)
    except Exception:
        pass

    return JsonResponse({
        'message': 'Registration successful',
        'user': {
            'id': user_id,
            'name': name,
            'email': email,
            'phone': phone,
            'role': role,
        },
        **tokens,
    }, status=201)


# ============================================================================
# POST /auth/login
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    """Login with email and password."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return JsonResponse({'error': 'Email and password are required'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, email, password_hash, phone, role, is_active
            FROM users WHERE email = %s
        """, [email])
        row = cursor.fetchone()

    if not row:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    user_id, name, user_email, password_hash, phone, role, is_active = row

    if not is_active:
        return JsonResponse({'error': 'Account is blocked. Contact support.'}, status=403)

    if not verify_password(password, password_hash):
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    tokens = generate_token_pair(user_id, role, user_email)

    return JsonResponse({
        'message': 'Login successful',
        'user': {
            'id': user_id,
            'name': name,
            'email': user_email,
            'phone': phone,
            'role': role,
        },
        **tokens,
    })


# ============================================================================
# POST /auth/refresh
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
def refresh_token(request):
    """Get new access token using refresh token."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    token = data.get('refresh_token', '')
    if not token:
        return JsonResponse({'error': 'refresh_token is required'}, status=400)

    try:
        payload = verify_token(token)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=401)

    if payload.get('token_type') != 'refresh':
        return JsonResponse({'error': 'Invalid token type. Use refresh token.'}, status=401)

    user_id = payload.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT email, role, is_active FROM users WHERE id = %s
        """, [user_id])
        row = cursor.fetchone()

    if not row:
        return JsonResponse({'error': 'User not found'}, status=404)

    email, role, is_active = row
    if not is_active:
        return JsonResponse({'error': 'Account is blocked'}, status=403)

    new_access = generate_access_token(user_id, role, email)

    return JsonResponse({
        'access_token': new_access,
        'token_type': 'Bearer',
    })


# ============================================================================
# GET /auth/me
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_auth
def get_profile(request):
    """Get current user's profile."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, email, phone, role, avatar_url, is_active, is_available, created_at
            FROM users WHERE id = %s
        """, [request.user_id])
        row = cursor.fetchone()

    if not row:
        return JsonResponse({'error': 'User not found'}, status=404)

    return JsonResponse({
        'id': row[0],
        'name': row[1],
        'email': row[2],
        'phone': row[3],
        'role': row[4],
        'avatar_url': row[5],
        'is_active': bool(row[6]),
        'is_available': bool(row[7]),
        'created_at': row[8].isoformat() if row[8] else None,
    })


# ============================================================================
# PUT /auth/me
# ============================================================================
@csrf_exempt
@require_http_methods(['PUT'])
@require_auth
def update_profile(request):
    """Update current user's profile (name, phone, avatar)."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    updates = []
    params = []

    if 'name' in data:
        name = data['name'].strip()
        if len(name) < 2:
            return JsonResponse({'error': 'Name must be at least 2 chars'}, status=400)
        updates.append('name = %s')
        params.append(name)

    if 'phone' in data:
        phone = data['phone'].strip()
        if not PHONE_REGEX.match(phone):
            return JsonResponse({'error': 'Invalid phone number'}, status=400)
        updates.append('phone = %s')
        params.append(phone)

    if 'avatar_url' in data:
        updates.append('avatar_url = %s')
        params.append(data['avatar_url'])

    if not updates:
        return JsonResponse({'error': 'No fields to update'}, status=400)

    params.append(request.user_id)
    sql = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
    except IntegrityError:
        return JsonResponse({'error': 'Phone already in use'}, status=409)

    # Invalidate user profile cache
    invalidate_user_profile(request.user_id)

    return JsonResponse({'message': 'Profile updated successfully'})


# ============================================================================
# POST /auth/change-password
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_auth
def change_password(request):
    """Change current user's password."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return JsonResponse({'error': 'old_password and new_password are required'}, status=400)
    if len(new_password) < 8:
        return JsonResponse({'error': 'New password must be at least 8 chars'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", [request.user_id])
        row = cursor.fetchone()

    if not row:
        return JsonResponse({'error': 'User not found'}, status=404)

    if not verify_password(old_password, row[0]):
        return JsonResponse({'error': 'Current password is incorrect'}, status=401)

    new_hash = hash_password(new_password)
    with connection.cursor() as cursor:
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s",
                       [new_hash, request.user_id])

    return JsonResponse({'message': 'Password changed successfully'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('auth/register', register, name='auth-register'),
    path('auth/login', login, name='auth-login'),
    path('auth/refresh', refresh_token, name='auth-refresh'),
    path('auth/me', get_profile, name='auth-me-get'),
    path('auth/me/update', update_profile, name='auth-me-update'),
    path('auth/change-password', change_password, name='auth-change-password'),
]

