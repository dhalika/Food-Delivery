"""
Auto-assignment logic - assign nearest available delivery partner to an order.
Called internally when restaurant accepts an order.
"""
import uuid
from math import radians, cos, sin, asin, sqrt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role, require_admin


def haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two points."""
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


def auto_assign_partner(order_id):
    """
    Core logic: Find nearest available delivery partner and assign them.
    Returns (success: bool, partner_id: str or None, message: str)
    """
    with connection.cursor() as cursor:
        # Get order details
        cursor.execute("""
            SELECT o.restaurant_id, r.lat, r.lng, o.delivery_partner_id
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE o.id = %s
        """, [order_id])
        order = cursor.fetchone()
        if not order:
            return False, None, 'Order not found'

        restaurant_id, rest_lat, rest_lng, existing_partner = order

        if existing_partner:
            return False, existing_partner, 'Partner already assigned'

        # Find all available partners not currently on active delivery
        cursor.execute("""
            SELECT u.id, u.name,
                   (SELECT lat FROM delivery_locations dl
                    WHERE dl.delivery_partner_id = u.id
                    ORDER BY updated_at DESC LIMIT 1) as last_lat,
                   (SELECT lng FROM delivery_locations dl
                    WHERE dl.delivery_partner_id = u.id
                    ORDER BY updated_at DESC LIMIT 1) as last_lng,
                   (SELECT COUNT(*) FROM orders o2
                    WHERE o2.delivery_partner_id = u.id
                    AND o2.status IN ('accepted', 'preparing', 'picked_up', 'out_for_delivery')
                   ) as active_count
            FROM users u
            WHERE u.role = 'delivery_partner'
                AND u.is_active = TRUE
                AND u.is_available = TRUE
            HAVING active_count = 0
        """)
        partners = cursor.fetchall()

        if not partners:
            return False, None, 'No delivery partners available'

        # Find nearest one with known location
        nearest = None
        min_distance = float('inf')

        for p in partners:
            if p[2] is None or p[3] is None:
                # No location known - skip or include as last resort
                continue
            d = haversine(rest_lat, rest_lng, p[2], p[3])
            if d < min_distance:
                min_distance = d
                nearest = p

        # If no partner has location, pick first available one
        if nearest is None and partners:
            nearest = partners[0]

        if nearest is None:
            return False, None, 'No suitable partner'

        partner_id = nearest[0]

        # Assign
        cursor.execute("""
            UPDATE orders SET delivery_partner_id = %s WHERE id = %s
        """, [partner_id, order_id])

        # Notify partner
        cursor.execute("""
            INSERT INTO notifications (id, user_id, title, message, type, reference_id)
            VALUES (%s, %s, %s, %s, 'order_update', %s)
        """, [
            str(uuid.uuid4()), partner_id, 'New Delivery Assignment',
            f'You have been assigned order #{order_id[:8]}.',
            order_id,
        ])

    return True, partner_id, 'Partner assigned successfully'


# ============================================================================
# POST /admin/orders/<id>/assign-partner - Admin manually assigns
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_admin
def admin_assign_partner(request, order_id):
    """Admin manually triggers auto-assignment for an order."""
    success, partner_id, message = auto_assign_partner(order_id)
    status_code = 200 if success else 400
    return JsonResponse({
        'success': success,
        'partner_id': partner_id,
        'message': message,
    }, status=status_code)


# ============================================================================
# POST /restaurant/orders/<id>/request-partner - Restaurant triggers assignment
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('restaurant_owner')
def request_partner(request, order_id):
    """Restaurant owner requests a delivery partner for order."""
    # Verify ownership
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT r.owner_id FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE o.id = %s
        """, [order_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Order not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': 'Not your order'}, status=403)

    success, partner_id, message = auto_assign_partner(order_id)
    status_code = 200 if success else 400
    return JsonResponse({
        'success': success,
        'partner_id': partner_id,
        'message': message,
    }, status=status_code)


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('admin/orders/<str:order_id>/assign-partner', admin_assign_partner, name='admin-assign'),
    path('restaurant/orders/<str:order_id>/request-partner', request_partner, name='restaurant-request-partner'),
]