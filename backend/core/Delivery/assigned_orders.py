"""
Delivery partner - view assigned orders.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role


# ============================================================================
# GET /delivery/orders - My assigned orders
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('delivery_partner')
def my_orders(request):
    """List orders assigned to current delivery partner."""
    status = request.GET.get('status')

    where = ['o.delivery_partner_id = %s']
    params = [request.user_id]

    if status:
        where.append('o.status = %s')
        params.append(status)
    else:
        # Default: only active orders
        where.append("o.status IN ('accepted', 'preparing', 'picked_up', 'out_for_delivery')")

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT o.id, o.status, o.final_amount, o.payment_method,
                   o.estimated_delivery_time, o.placed_at, o.accepted_at,
                   r.id, r.name, r.phone, r.address, r.lat, r.lng,
                   c.name, c.phone,
                   a.full_address, a.city, a.pincode, a.lat, a.lng
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            JOIN users c ON c.id = o.customer_id
            JOIN addresses a ON a.id = o.delivery_address_id
            WHERE {' AND '.join(where)}
            ORDER BY o.placed_at DESC
        """, params)

        orders = [
            {
                'id': row[0],
                'status': row[1],
                'final_amount': float(row[2]),
                'payment_method': row[3],
                'estimated_delivery_time': row[4],
                'placed_at': row[5].isoformat() if row[5] else None,
                'accepted_at': row[6].isoformat() if row[6] else None,
                'restaurant': {
                    'id': row[7],
                    'name': row[8],
                    'phone': row[9],
                    'address': row[10],
                    'lat': float(row[11]) if row[11] else None,
                    'lng': float(row[12]) if row[12] else None,
                },
                'customer': {
                    'name': row[13],
                    'phone': row[14],
                },
                'delivery_address': {
                    'full_address': row[15],
                    'city': row[16],
                    'pincode': row[17],
                    'lat': float(row[18]) if row[18] else None,
                    'lng': float(row[19]) if row[19] else None,
                },
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({'orders': orders})


# ============================================================================
# GET /delivery/orders/<id> - Order details
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('delivery_partner')
def order_detail(request, order_id):
    """Full order details for delivery partner."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.id, o.status, o.item_total, o.discount_amount, o.final_amount,
                   o.payment_method, o.special_instructions,
                   o.placed_at, o.accepted_at, o.picked_up_at, o.delivered_at,
                   o.estimated_delivery_time,
                   r.id, r.name, r.phone, r.address, r.city, r.lat, r.lng,
                   c.name, c.phone,
                   a.full_address, a.city, a.pincode, a.lat, a.lng
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            JOIN users c ON c.id = o.customer_id
            JOIN addresses a ON a.id = o.delivery_address_id
            WHERE o.id = %s AND o.delivery_partner_id = %s
        """, [order_id, request.user_id])

        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Order not found or not assigned to you'}, status=404)

        cursor.execute("""
            SELECT item_name, item_price, quantity, subtotal
            FROM order_items WHERE order_id = %s
        """, [order_id])
        items = [
            {'name': r[0], 'price': float(r[1]), 'quantity': r[2], 'subtotal': float(r[3])}
            for r in cursor.fetchall()
        ]

    return JsonResponse({
        'id': row[0],
        'status': row[1],
        'item_total': float(row[2]),
        'discount_amount': float(row[3]),
        'final_amount': float(row[4]),
        'payment_method': row[5],
        'special_instructions': row[6],
        'placed_at': row[7].isoformat() if row[7] else None,
        'accepted_at': row[8].isoformat() if row[8] else None,
        'picked_up_at': row[9].isoformat() if row[9] else None,
        'delivered_at': row[10].isoformat() if row[10] else None,
        'estimated_delivery_time': row[11],
        'restaurant': {
            'id': row[12], 'name': row[13], 'phone': row[14],
            'address': row[15], 'city': row[16],
            'lat': float(row[17]) if row[17] else None,
            'lng': float(row[18]) if row[18] else None,
        },
        'customer': {'name': row[19], 'phone': row[20]},
        'delivery_address': {
            'full_address': row[21], 'city': row[22], 'pincode': row[23],
            'lat': float(row[24]) if row[24] else None,
            'lng': float(row[25]) if row[25] else None,
        },
        'items': items,
    })


# ============================================================================
# GET /delivery/history - Completed deliveries history
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('delivery_partner')
def delivery_history(request):
    """Past completed deliveries with stats."""
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders
            WHERE delivery_partner_id = %s AND status = 'delivered'
        """, [request.user_id])
        total_deliveries, total_revenue = cursor.fetchone()

        # Today's stats
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders
            WHERE delivery_partner_id = %s AND status = 'delivered'
                AND DATE(delivered_at) = CURDATE()
        """, [request.user_id])
        today_deliveries, today_revenue = cursor.fetchone()

        # Recent deliveries
        cursor.execute("""
            SELECT o.id, o.final_amount, o.delivered_at, r.name
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE o.delivery_partner_id = %s AND o.status = 'delivered'
            ORDER BY o.delivered_at DESC
            LIMIT %s OFFSET %s
        """, [request.user_id, limit, offset])

        deliveries = [
            {
                'order_id': r[0],
                'amount': float(r[1]),
                'delivered_at': r[2].isoformat() if r[2] else None,
                'restaurant_name': r[3],
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({
        'stats': {
            'total_deliveries': total_deliveries,
            'total_revenue_handled': float(total_revenue),
            'today_deliveries': today_deliveries,
            'today_revenue_handled': float(today_revenue),
        },
        'deliveries': deliveries,
    })


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('delivery/orders', my_orders, name='delivery-orders'),
    path('delivery/orders/<str:order_id>', order_detail, name='delivery-order-detail'),
    path('delivery/history', delivery_history, name='delivery-history'),
]