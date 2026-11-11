"""
Incoming orders - view, accept, reject, mark preparing.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection, transaction
from django.utils import timezone

from auth.guards import require_role
from core.WebSocket.broadcasters import broadcast_order_status


def _verify_order_belongs_to_owner(order_id, user_id):
    """Check if order belongs to a restaurant owned by user."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.status, o.restaurant_id, r.owner_id
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE o.id = %s
        """, [order_id])
        row = cursor.fetchone()
        if not row:
            return False, 'Order not found', None
        if row[2] != user_id:
            return False, 'Not your order', None
        return True, None, row[0]  # status


# ============================================================================
# GET /restaurant/orders - List orders for my restaurants
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('restaurant_owner')
def list_incoming_orders(request):
    """List orders for all restaurants owned by current user."""
    status = request.GET.get('status')
    restaurant_id = request.GET.get('restaurant_id')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit

    where = ['r.owner_id = %s']
    params = [request.user_id]

    if status:
        where.append('o.status = %s')
        params.append(status)
    if restaurant_id:
        where.append('o.restaurant_id = %s')
        params.append(restaurant_id)

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE {' AND '.join(where)}
        """, params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT o.id, o.status, o.final_amount, o.payment_method,
                   o.special_instructions, o.placed_at,
                   c.name as customer_name, c.phone as customer_phone,
                   r.name as restaurant_name,
                   (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
            FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            JOIN users c ON c.id = o.customer_id
            WHERE {' AND '.join(where)}
            ORDER BY o.placed_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        orders = [
            {
                'id': row[0],
                'status': row[1],
                'final_amount': float(row[2]),
                'payment_method': row[3],
                'special_instructions': row[4],
                'placed_at': row[5].isoformat() if row[5] else None,
                'customer_name': row[6],
                'customer_phone': row[7],
                'restaurant_name': row[8],
                'item_count': row[9],
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({'total': total, 'page': page, 'orders': orders})


# ============================================================================
# GET /restaurant/orders/<id> - Order details
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('restaurant_owner')
def get_order(request, order_id):
    """Order details (owner view)."""
    ok, err, _ = _verify_order_belongs_to_owner(order_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.id, o.status, o.item_total, o.discount_amount,
                   o.delivery_fee, o.tax_amount, o.final_amount,
                   o.payment_method, o.special_instructions, o.placed_at,
                   o.accepted_at, o.estimated_delivery_time,
                   c.name, c.phone, c.email,
                   a.full_address, a.city, a.pincode, a.lat, a.lng
            FROM orders o
            JOIN users c ON c.id = o.customer_id
            JOIN addresses a ON a.id = o.delivery_address_id
            WHERE o.id = %s
        """, [order_id])
        row = cursor.fetchone()

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
        'delivery_fee': float(row[4]),
        'tax_amount': float(row[5]),
        'final_amount': float(row[6]),
        'payment_method': row[7],
        'special_instructions': row[8],
        'placed_at': row[9].isoformat() if row[9] else None,
        'accepted_at': row[10].isoformat() if row[10] else None,
        'estimated_delivery_time': row[11],
        'customer': {'name': row[12], 'phone': row[13], 'email': row[14]},
        'delivery_address': {
            'full_address': row[15], 'city': row[16], 'pincode': row[17],
            'lat': float(row[18]) if row[18] else None,
            'lng': float(row[19]) if row[19] else None,
        },
        'items': items,
    })


# ============================================================================
# PATCH /restaurant/orders/<id>/accept - Accept order (triggers auto-assignment)
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('restaurant_owner')
def accept_order(request, order_id):
    """Accept an incoming order and auto-assign nearest delivery partner."""
    ok, err, status = _verify_order_belongs_to_owner(order_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)
    if status != 'placed':
        return JsonResponse({'error': f'Cannot accept order in status: {status}'}, status=400)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    est_time = data.get('estimated_delivery_time', 30)

    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE orders SET status = 'accepted', accepted_at = %s,
                                  estimated_delivery_time = %s
                WHERE id = %s
            """, [now, est_time, order_id])

            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, changed_at)
                VALUES (%s, %s, 'accepted', %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, now])

    # Broadcast status change to WebSocket subscribers
    broadcast_order_status(order_id, 'accepted')

    # Auto-assign nearest delivery partner
    from core.Delivery.auto_assignment import auto_assign_partner
    assign_success, partner_id, assign_msg = auto_assign_partner(order_id)

    return JsonResponse({
        'message': 'Order accepted',
        'status': 'accepted',
        'partner_assigned': assign_success,
        'partner_id': partner_id,
        'assign_message': assign_msg,
    })


# ============================================================================
# PATCH /restaurant/orders/<id>/preparing - Mark preparing
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('restaurant_owner')
def mark_preparing(request, order_id):
    """Mark order as preparing."""
    ok, err, status = _verify_order_belongs_to_owner(order_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)
    if status != 'accepted':
        return JsonResponse({'error': f'Cannot mark preparing from status: {status}'}, status=400)

    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("UPDATE orders SET status = 'preparing' WHERE id = %s", [order_id])
            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, changed_at)
                VALUES (%s, %s, 'preparing', %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, now])

    # Broadcast status change
    broadcast_order_status(order_id, 'preparing')

    return JsonResponse({'message': 'Order preparing', 'status': 'preparing'})


# ============================================================================
# PATCH /restaurant/orders/<id>/reject - Reject order
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('restaurant_owner')
def reject_order(request, order_id):
    """Reject an order with reason."""
    ok, err, status = _verify_order_belongs_to_owner(order_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)
    if status != 'placed':
        return JsonResponse({'error': f'Cannot reject order in status: {status}'}, status=400)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    reason = data.get('reason', 'Rejected by restaurant')

    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE orders SET status = 'cancelled', cancelled_at = %s,
                    cancel_reason = %s, cancelled_by = 'restaurant'
                WHERE id = %s
            """, [now, reason, order_id])

            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, note, changed_at)
                VALUES (%s, %s, 'cancelled', %s, %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, reason, now])

    # Broadcast cancellation
    broadcast_order_status(order_id, 'cancelled', note=reason)

    return JsonResponse({'message': 'Order rejected'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurant/orders', list_incoming_orders, name='restaurant-orders-list'),
    path('restaurant/orders/<str:order_id>', get_order, name='restaurant-order-detail'),
    path('restaurant/orders/<str:order_id>/accept', accept_order, name='restaurant-order-accept'),
    path('restaurant/orders/<str:order_id>/preparing', mark_preparing, name='restaurant-order-preparing'),
    path('restaurant/orders/<str:order_id>/reject', reject_order, name='restaurant-order-reject'),
]