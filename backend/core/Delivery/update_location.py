"""
Delivery partner GPS location updates.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role
from core.WebSocket.broadcasters import broadcast_location


# ============================================================================
# POST /delivery/location - Push current GPS location
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('delivery_partner')
def update_location(request):
    """
    Update delivery partner's current GPS location for an active order.
    Body: { "order_id": "...", "lat": 17.5, "lng": 78.5 }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    order_id = data.get('order_id')
    lat = data.get('lat')
    lng = data.get('lng')

    if not order_id or lat is None or lng is None:
        return JsonResponse({'error': 'order_id, lat, lng required'}, status=400)

    # Verify order is assigned to this partner and active
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT status FROM orders
            WHERE id = %s AND delivery_partner_id = %s
        """, [order_id, request.user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Order not found or not assigned to you'}, status=404)
        if row[0] not in ('accepted', 'preparing', 'picked_up', 'out_for_delivery'):
            return JsonResponse({'error': f'Cannot update location for status: {row[0]}'}, status=400)

        # Insert new location record
        cursor.execute("""
            INSERT INTO delivery_locations (id, delivery_partner_id, order_id, lat, lng)
            VALUES (%s, %s, %s, %s, %s)
        """, [str(uuid.uuid4()), request.user_id, order_id, lat, lng])

    # Broadcast to customers tracking this order
    broadcast_location(order_id, lat, lng)

    return JsonResponse({
        'message': 'Location updated',
        'lat': float(lat),
        'lng': float(lng),
    })


# ============================================================================
# GET /delivery/location/<order_id>/history - Location trail for order
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('delivery_partner')
def location_history(request, order_id):
    """Get location trail for an order."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id FROM orders
            WHERE id = %s AND delivery_partner_id = %s
        """, [order_id, request.user_id])
        if not cursor.fetchone():
            return JsonResponse({'error': 'Order not found or not assigned to you'}, status=404)

        cursor.execute("""
            SELECT lat, lng, updated_at
            FROM delivery_locations
            WHERE order_id = %s
            ORDER BY updated_at
        """, [order_id])

        trail = [
            {
                'lat': float(r[0]),
                'lng': float(r[1]),
                'timestamp': r[2].isoformat() if r[2] else None,
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({'order_id': order_id, 'trail': trail})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('delivery/location', update_location, name='delivery-location-update'),
    path('delivery/location/<str:order_id>/history', location_history, name='delivery-location-history'),
]