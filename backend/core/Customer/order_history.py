"""
Order history - list, detail, status history.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role
from core.WebSocket.broadcasters import broadcast_order_status


# ============================================================================
# GET /orders - My orders (customer)
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def my_orders(request):
    """List my orders."""
    status = request.GET.get('status')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit

    where = ['o.customer_id = %s']
    params = [request.user_id]
    if status:
        where.append('o.status = %s')
        params.append(status)

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM orders o WHERE {' AND '.join(where)}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT o.id, o.status, o.final_amount, o.payment_method,
                   o.placed_at, o.delivered_at,
                   r.name as restaurant_name, r.logo_url,
                   (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE {' AND '.join(where)}
            ORDER BY o.placed_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        orders = [
            {
                'id': r[0],
                'status': r[1],
                'final_amount': float(r[2]),
                'payment_method': r[3],
                'placed_at': r[4].isoformat() if r[4] else None,
                'delivered_at': r[5].isoformat() if r[5] else None,
                'restaurant_name': r[6],
                'restaurant_logo': r[7],
                'item_count': r[8],
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({'total': total, 'page': page, 'orders': orders})


# ============================================================================
# GET /orders/<id> - Order details
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def order_detail(request, order_id):
    """Full order details."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.id, o.status, o.item_total, o.discount_amount, o.delivery_fee,
                   o.tax_amount, o.final_amount, o.payment_method,
                   o.special_instructions, o.cancel_reason,
                   o.placed_at, o.accepted_at, o.picked_up_at, o.delivered_at, o.cancelled_at,
                   o.estimated_delivery_time,
                   r.id, r.name, r.phone, r.logo_url,
                   dp.id, dp.name, dp.phone,
                   a.full_address, a.city, a.pincode
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            LEFT JOIN users dp ON dp.id = o.delivery_partner_id
            JOIN addresses a ON a.id = o.delivery_address_id
            WHERE o.id = %s AND o.customer_id = %s
        """, [order_id, request.user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Order not found'}, status=404)

        # Items
        cursor.execute("""
            SELECT item_name, item_price, quantity, subtotal
            FROM order_items WHERE order_id = %s
        """, [order_id])
        items = [
            {'name': r[0], 'price': float(r[1]), 'quantity': r[2], 'subtotal': float(r[3])}
            for r in cursor.fetchall()
        ]

        # Payment
        cursor.execute("""
            SELECT method, status, paid_at FROM payments WHERE order_id = %s
        """, [order_id])
        p = cursor.fetchone()
        payment = {
            'method': p[0], 'status': p[1],
            'paid_at': p[2].isoformat() if p[2] else None,
        } if p else None

    return JsonResponse({
        'id': row[0],
        'status': row[1],
        'item_total': float(row[2]),
        'discount_amount': float(row[3]),
        'delivery_fee': float(row[4]),
        'tax_amount': float(row[5]),
        'final_amount': float(row[6]),
        'payment_method': row[7],
        'special_instructions': row[8],
        'cancel_reason': row[9],
        'placed_at': row[10].isoformat() if row[10] else None,
        'accepted_at': row[11].isoformat() if row[11] else None,
        'picked_up_at': row[12].isoformat() if row[12] else None,
        'delivered_at': row[13].isoformat() if row[13] else None,
        'cancelled_at': row[14].isoformat() if row[14] else None,
        'estimated_delivery_time': row[15],
        'restaurant': {
            'id': row[16], 'name': row[17], 'phone': row[18], 'logo_url': row[19],
        },
        'delivery_partner': {
            'id': row[20], 'name': row[21], 'phone': row[22],
        } if row[20] else None,
        'delivery_address': {
            'full_address': row[23], 'city': row[24], 'pincode': row[25],
        },
        'items': items,
        'payment': payment,
    })


# ============================================================================
# GET /orders/<id>/status-history - Status timeline
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def status_history(request, order_id):
    """Status change timeline."""
    with connection.cursor() as cursor:
        # Verify ownership
        cursor.execute("""
            SELECT id FROM orders WHERE id = %s AND customer_id = %s
        """, [order_id, request.user_id])
        if not cursor.fetchone():
            return JsonResponse({'error': 'Order not found'}, status=404)

        cursor.execute("""
            SELECT status, note, changed_at
            FROM order_status_history
            WHERE order_id = %s
            ORDER BY changed_at
        """, [order_id])
        history = [
            {
                'status': r[0],
                'note': r[1],
                'timestamp': r[2].isoformat() if r[2] else None,
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({'order_id': order_id, 'history': history})


# ============================================================================
# PATCH /orders/<id>/cancel - Cancel order
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('customer')
def cancel_order(request, order_id):
    """Customer cancels their own order (only if not accepted yet)."""
    import json, uuid
    from django.utils import timezone
    from django.db import transaction

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    reason = data.get('reason', 'Cancelled by customer')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT status FROM orders WHERE id = %s AND customer_id = %s
        """, [order_id, request.user_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Order not found'}, status=404)
        if row[0] not in ('placed',):
            return JsonResponse({'error': f'Cannot cancel order in status: {row[0]}'}, status=400)

        now = timezone.now()
        with transaction.atomic():
            cursor.execute("""
                UPDATE orders SET status = 'cancelled', cancelled_at = %s,
                    cancel_reason = %s, cancelled_by = 'customer'
                WHERE id = %s
            """, [now, reason, order_id])

            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, note, changed_at)
                VALUES (%s, %s, 'cancelled', %s, %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, reason, now])

    # Broadcast cancellation to WebSocket subscribers
    broadcast_order_status(order_id, 'cancelled', note=reason)

    return JsonResponse({'message': 'Order cancelled'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('orders', my_orders, name='my-orders'),
    path('orders/<str:order_id>', order_detail, name='order-detail'),
    path('orders/<str:order_id>/status-history', status_history, name='order-status-history'),
    path('orders/<str:order_id>/cancel', cancel_order, name='customer-order-cancel'),
]