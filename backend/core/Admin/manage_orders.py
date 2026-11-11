"""
Admin order management - view all orders, cancel, refund.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection, transaction
from django.utils import timezone

from auth.guards import require_admin
from core.WebSocket.broadcasters import broadcast_order_status


# ============================================================================
# GET /admin/orders - List all orders with filters
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def list_orders(request):
    """
    List orders with filters.
    Query params: status, restaurant_id, customer_id, from_date, to_date, page, limit
    """
    status = request.GET.get('status')
    restaurant_id = request.GET.get('restaurant_id')
    customer_id = request.GET.get('customer_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit

    where_clauses = []
    params = []

    if status:
        where_clauses.append('o.status = %s')
        params.append(status)
    if restaurant_id:
        where_clauses.append('o.restaurant_id = %s')
        params.append(restaurant_id)
    if customer_id:
        where_clauses.append('o.customer_id = %s')
        params.append(customer_id)
    if from_date:
        where_clauses.append('DATE(o.placed_at) >= %s')
        params.append(from_date)
    if to_date:
        where_clauses.append('DATE(o.placed_at) <= %s')
        params.append(to_date)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM orders o {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT
                o.id, o.status, o.final_amount, o.payment_method, o.placed_at,
                c.name as customer_name, c.phone as customer_phone,
                r.name as restaurant_name, r.city,
                dp.name as delivery_partner_name
            FROM orders o
            LEFT JOIN users c ON c.id = o.customer_id
            LEFT JOIN restaurants r ON r.id = o.restaurant_id
            LEFT JOIN users dp ON dp.id = o.delivery_partner_id
            {where_sql}
            ORDER BY o.placed_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        orders = [
            {
                'id': row[0],
                'status': row[1],
                'final_amount': float(row[2]),
                'payment_method': row[3],
                'placed_at': row[4].isoformat() if row[4] else None,
                'customer_name': row[5],
                'customer_phone': row[6],
                'restaurant_name': row[7],
                'city': row[8],
                'delivery_partner_name': row[9],
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({
        'total': total,
        'page': page,
        'limit': limit,
        'orders': orders,
    })


# ============================================================================
# GET /admin/orders/<id> - Full order details
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def get_order_details(request, order_id):
    """Full order details including items, status history, payment."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                o.id, o.status, o.item_total, o.discount_amount, o.delivery_fee,
                o.tax_amount, o.final_amount, o.payment_method,
                o.special_instructions, o.cancel_reason, o.cancelled_by,
                o.placed_at, o.accepted_at, o.picked_up_at, o.delivered_at, o.cancelled_at,
                c.id as customer_id, c.name as customer_name, c.email as customer_email, c.phone as customer_phone,
                r.id as restaurant_id, r.name as restaurant_name, r.city, r.phone as restaurant_phone,
                dp.id as dp_id, dp.name as dp_name, dp.phone as dp_phone,
                a.full_address, a.city as del_city, a.pincode
            FROM orders o
            LEFT JOIN users c ON c.id = o.customer_id
            LEFT JOIN restaurants r ON r.id = o.restaurant_id
            LEFT JOIN users dp ON dp.id = o.delivery_partner_id
            LEFT JOIN addresses a ON a.id = o.delivery_address_id
            WHERE o.id = %s
        """, [order_id])

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

        # Status history
        cursor.execute("""
            SELECT status, note, changed_at FROM order_status_history
            WHERE order_id = %s ORDER BY changed_at
        """, [order_id])
        history = [
            {'status': r[0], 'note': r[1], 'changed_at': r[2].isoformat() if r[2] else None}
            for r in cursor.fetchall()
        ]

        # Payment
        cursor.execute("""
            SELECT method, amount, status, razorpay_payment_id, paid_at
            FROM payments WHERE order_id = %s
        """, [order_id])
        payment_row = cursor.fetchone()
        payment = None
        if payment_row:
            payment = {
                'method': payment_row[0],
                'amount': float(payment_row[1]),
                'status': payment_row[2],
                'razorpay_payment_id': payment_row[3],
                'paid_at': payment_row[4].isoformat() if payment_row[4] else None,
            }

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
        'cancelled_by': row[10],
        'placed_at': row[11].isoformat() if row[11] else None,
        'accepted_at': row[12].isoformat() if row[12] else None,
        'picked_up_at': row[13].isoformat() if row[13] else None,
        'delivered_at': row[14].isoformat() if row[14] else None,
        'cancelled_at': row[15].isoformat() if row[15] else None,
        'customer': {'id': row[16], 'name': row[17], 'email': row[18], 'phone': row[19]},
        'restaurant': {'id': row[20], 'name': row[21], 'city': row[22], 'phone': row[23]},
        'delivery_partner': {'id': row[24], 'name': row[25], 'phone': row[26]} if row[24] else None,
        'delivery_address': {'full_address': row[27], 'city': row[28], 'pincode': row[29]},
        'items': items,
        'status_history': history,
        'payment': payment,
    })


# ============================================================================
# PATCH /admin/orders/<id>/cancel - Admin force-cancel an order
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_admin
def cancel_order(request, order_id):
    """Admin can force-cancel any order."""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    reason = data.get('reason', 'Cancelled by admin')

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT status FROM orders WHERE id = %s", [order_id])
            row = cursor.fetchone()

            if not row:
                return JsonResponse({'error': 'Order not found'}, status=404)

            if row[0] in ('delivered', 'cancelled'):
                return JsonResponse({'error': f'Cannot cancel order in status: {row[0]}'}, status=400)

            now = timezone.now()
            cursor.execute("""
                UPDATE orders SET
                    status = 'cancelled',
                    cancel_reason = %s,
                    cancelled_by = 'admin',
                    cancelled_at = %s
                WHERE id = %s
            """, [reason, now, order_id])

            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, note, changed_at)
                VALUES (UUID(), %s, 'cancelled', %s, %s, %s)
            """, [order_id, request.user_id, reason, now])

    # Broadcast cancellation
    broadcast_order_status(order_id, 'cancelled', note=reason)

    return JsonResponse({'message': 'Order cancelled successfully'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('admin/orders', list_orders, name='admin-orders-list'),
    path('admin/orders/<str:order_id>', get_order_details, name='admin-order-detail'),
    path('admin/orders/<str:order_id>/cancel', cancel_order, name='admin-order-cancel'),
]