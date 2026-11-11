"""
Restaurant owner - create, update, toggle restaurant profile.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role, require_auth
from core.Cache.cache_invalidation import invalidate_restaurant
from core.Cache.cache_service import cache_delete
from core.Cache.cache_keys import RESTAURANT_LIST


# ============================================================================
# POST /restaurants - Create a new restaurant
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('restaurant_owner')
def create_restaurant(request):
    """Owner creates a new restaurant."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    cuisine_type = data.get('cuisine_type', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    city = data.get('city', '').strip()
    pincode = data.get('pincode', '').strip()
    lat = data.get('lat')
    lng = data.get('lng')

    if not name or len(name) < 2:
        return JsonResponse({'error': 'Restaurant name is required'}, status=400)
    if not cuisine_type:
        return JsonResponse({'error': 'cuisine_type is required'}, status=400)
    if not phone or not address or not city or not pincode:
        return JsonResponse({'error': 'phone, address, city, pincode are required'}, status=400)
    if lat is None or lng is None:
        return JsonResponse({'error': 'lat and lng are required'}, status=400)

    restaurant_id = str(uuid.uuid4())

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO restaurants (
                id, owner_id, name, description, cuisine_type, phone, email,
                logo_url, banner_url, address, city, pincode, lat, lng,
                min_order_value, is_active, is_verified
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, FALSE)
        """, [
            restaurant_id, request.user_id, name,
            data.get('description'), cuisine_type, phone,
            data.get('email'), data.get('logo_url'), data.get('banner_url'),
            address, city, pincode, lat, lng,
            data.get('min_order_value', 0),
        ])

    # Invalidate restaurant list cache
    cache_delete(RESTAURANT_LIST)

    return JsonResponse({
        'id': restaurant_id,
        'message': 'Restaurant created. Pending admin verification.',
    }, status=201)


# ============================================================================
# GET /restaurants/me - My restaurants
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('restaurant_owner')
def my_restaurants(request):
    """List restaurants owned by current user."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, cuisine_type, city, avg_rating, total_reviews,
                   is_active, is_verified, created_at
            FROM restaurants WHERE owner_id = %s
            ORDER BY created_at DESC
        """, [request.user_id])

        restaurants = [
            {
                'id': row[0],
                'name': row[1],
                'cuisine_type': row[2],
                'city': row[3],
                'avg_rating': float(row[4]) if row[4] else 0,
                'total_reviews': row[5],
                'is_active': bool(row[6]),
                'is_verified': bool(row[7]),
                'created_at': row[8].isoformat() if row[8] else None,
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({'restaurants': restaurants})


# ============================================================================
# PUT /restaurants/<id> - Update restaurant
# ============================================================================
@csrf_exempt
@require_http_methods(['PUT'])
@require_role('restaurant_owner')
def update_restaurant(request, restaurant_id):
    """Update restaurant profile."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("SELECT owner_id FROM restaurants WHERE id = %s", [restaurant_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': 'Not your restaurant'}, status=403)

    allowed = {
        'name', 'description', 'cuisine_type', 'phone', 'email',
        'logo_url', 'banner_url', 'address', 'city', 'pincode',
        'lat', 'lng', 'avg_delivery_time', 'min_order_value'
    }

    updates = []
    params = []
    for field in allowed:
        if field in data:
            updates.append(f'{field} = %s')
            params.append(data[field])

    if not updates:
        return JsonResponse({'error': 'No fields to update'}, status=400)

    params.append(restaurant_id)
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE restaurants SET {', '.join(updates)} WHERE id = %s", params)

    # Invalidate all restaurant caches
    invalidate_restaurant(restaurant_id)

    return JsonResponse({'message': 'Restaurant updated successfully'})


# ============================================================================
# PATCH /restaurants/<id>/toggle-active - Go online/offline
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('restaurant_owner')
def toggle_active(request, restaurant_id):
    """Owner toggles restaurant active status."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT owner_id, is_active FROM restaurants WHERE id = %s
        """, [restaurant_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': 'Not your restaurant'}, status=403)

        new_status = not bool(row[1])
        cursor.execute("UPDATE restaurants SET is_active = %s WHERE id = %s",
                       [new_status, restaurant_id])

    # Invalidate restaurant caches
    invalidate_restaurant(restaurant_id)

    return JsonResponse({
        'restaurant_id': restaurant_id,
        'is_active': new_status,
    })


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurants/create', create_restaurant, name='restaurant-create'),
    path('restaurants/me', my_restaurants, name='my-restaurants'),
    path('restaurants/<str:restaurant_id>/update', update_restaurant, name='restaurant-update'),
    path('restaurants/<str:restaurant_id>/toggle-active', toggle_active, name='restaurant-toggle'),
]