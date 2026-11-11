"""
Track order - live delivery partner location.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role


# ============================================================================
# GET /orders/<id>/track - Get latest delivery location
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def track_order(request, order_id):
    """Get real-time location of delivery partner."""
    with connection.cursor() as cursor:
        # Verify ownership
        cursor.execute("""
            SELECT o.status, o.delivery_partner_id, dp.name, dp.phone,
                   r.lat as rest_lat, r.lng as rest_lng, r.name as rest_name,
                   a.lat as del_lat, a.lng as del_lng, a.full_address
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            JOIN addresses a ON a.id = o.delivery_address_id
            LEFT JOIN users dp ON dp.id = o.delivery_partner_id
            WHERE o.id = %s AND o.customer_id = %s
        """, [order_id, request.user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Order not found'}, status=404)

        status, dp_id, dp_name, dp_phone = row[0], row[1], row[2], row[3]

        result = {
            'order_id': order_id,
            'status': status,
            'restaurant': {
                'name': row[6],
                'lat': float(row[4]) if row[4] else None,
                'lng': float(row[5]) if row[5] else None,
            },
            'delivery_address': {
                'full_address': row[9],
                'lat': float(row[7]) if row[7] else None,
                'lng': float(row[8]) if row[8] else None,
            },
            'delivery_partner': None,
            'current_location': None,
        }

        if dp_id:
            result['delivery_partner'] = {
                'id': dp_id, 'name': dp_name, 'phone': dp_phone,
            }

            # Get latest location
            cursor.execute("""
                SELECT lat, lng, updated_at
                FROM delivery_locations
                WHERE order_id = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """, [order_id])
            loc = cursor.fetchone()
            if loc:
                result['current_location'] = {
                    'lat': float(loc[0]),
                    'lng': float(loc[1]),
                    'updated_at': loc[2].isoformat() if loc[2] else None,
                }

    return JsonResponse(result)


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('orders/<str:order_id>/track', track_order, name='order-track'),
]