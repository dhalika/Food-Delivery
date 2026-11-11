"""
Customer addresses - CRUD for delivery addresses.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role
from core.Cache.cache_invalidation import invalidate_user_addresses


# ============================================================================
# POST /customer/addresses - Add address
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def add_address(request):
    """Add a new delivery address."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    label = data.get('label', 'home').strip()
    full_address = data.get('full_address', '').strip()
    city = data.get('city', '').strip()
    state = data.get('state', '').strip()
    pincode = data.get('pincode', '').strip()
    lat = data.get('lat')
    lng = data.get('lng')
    is_default = data.get('is_default', False)

    if not full_address or not city or not state or not pincode:
        return JsonResponse({'error': 'full_address, city, state, pincode required'}, status=400)

    address_id = str(uuid.uuid4())

    with connection.cursor() as cursor:
        if is_default:
            cursor.execute(
                "UPDATE addresses SET is_default = FALSE WHERE user_id = %s",
                [request.user_id]
            )

        cursor.execute("""
            INSERT INTO addresses (id, user_id, label, full_address, city, state,
                                   pincode, lat, lng, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [address_id, request.user_id, label, full_address, city, state,
              pincode, lat, lng, is_default])

    invalidate_user_addresses(request.user_id)

    return JsonResponse({'id': address_id, 'message': 'Address added'}, status=201)


# ============================================================================
# GET /customer/addresses - List my addresses
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def list_addresses(request):
    """List all addresses for current user."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, label, full_address, city, state, pincode,
                   lat, lng, is_default, created_at
            FROM addresses WHERE user_id = %s
            ORDER BY is_default DESC, created_at DESC
        """, [request.user_id])

        addresses = [
            {
                'id': row[0],
                'label': row[1],
                'full_address': row[2],
                'city': row[3],
                'state': row[4],
                'pincode': row[5],
                'lat': float(row[6]) if row[6] else None,
                'lng': float(row[7]) if row[7] else None,
                'is_default': bool(row[8]),
                'created_at': row[9].isoformat() if row[9] else None,
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({'addresses': addresses})


# ============================================================================
# PUT /customer/addresses/<id> - Update address
# ============================================================================
@csrf_exempt
@require_http_methods(['PUT'])
@require_role('customer')
def update_address(request, address_id):
    """Update an address."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("SELECT user_id FROM addresses WHERE id = %s", [address_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Address not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': 'Not your address'}, status=403)

    allowed = {'label', 'full_address', 'city', 'state', 'pincode', 'lat', 'lng', 'is_default'}
    updates = []
    params = []
    for field in allowed:
        if field in data:
            updates.append(f'{field} = %s')
            params.append(data[field])

    if not updates:
        return JsonResponse({'error': 'No fields to update'}, status=400)

    with connection.cursor() as cursor:
        if data.get('is_default'):
            cursor.execute(
                "UPDATE addresses SET is_default = FALSE WHERE user_id = %s",
                [request.user_id]
            )

        params.append(address_id)
        cursor.execute(f"UPDATE addresses SET {', '.join(updates)} WHERE id = %s", params)

    invalidate_user_addresses(request.user_id)

    return JsonResponse({'message': 'Address updated'})


# ============================================================================
# DELETE /customer/addresses/<id> - Delete address
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_role('customer')
def delete_address(request, address_id):
    """Delete an address."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT user_id FROM addresses WHERE id = %s", [address_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Address not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': 'Not your address'}, status=403)

        cursor.execute("DELETE FROM addresses WHERE id = %s", [address_id])

    invalidate_user_addresses(request.user_id)

    return JsonResponse({'message': 'Address deleted'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('customer/addresses', list_addresses, name='customer-addresses-list'),
    path('customer/addresses/add', add_address, name='customer-address-add'),
    path('customer/addresses/<str:address_id>/update', update_address, name='customer-address-update'),
    path('customer/addresses/<str:address_id>/delete', delete_address, name='customer-address-delete'),
]