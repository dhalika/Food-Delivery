"""
Delivery partner - pickup, mark out for delivery, deliver.
"""
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection, transaction
from django.utils import timezone

from auth.guards import require_role
from core.WebSocket.broadcasters import broadcast_order_status


def _verify_assignment(order_id, user_id):
    """Verify order is assigned to this delivery partner."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT status, delivery_partner_id, customer_id, restaurant_id
            FROM orders WHERE id = %s
        """, [order_id])
        row = cursor.fetchone()
        if not row:
            return False, 'Order not found', None, None, None
        if row[1] != user_id:
            return False, 'Not assigned to you', None, None, None
        return True, None, row[0], row[2], row[3]


def _notify(user_id, title, message, order_id):
    """Create a notification."""
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO notifications (id, user_id, title, message, type, reference_id)
            VALUES (%s, %s, %s, %s, 'order_update', %s)
        """, [str(uuid.uuid4()), user_id, title, message, order_id])


# ============================================================================
# PATCH /delivery/orders/<id>/pickup - Mark picked up from restaurant
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('delivery_partner')
def pickup_order(request, order_id):
    """Delivery partner picks up order from restaurant."""
    ok, err, status, customer_id, _ = _verify_assignment(order_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'assigned' in err else 404)
    if status != 'preparing':
        return JsonResponse({'error': f'Cannot pick up order in status: {status}'}, status=400)

    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE orders SET status = 'picked_up', picked_up_at = %s WHERE id = %s
            """, [now, order_id])

            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, changed_at)
                VALUES (%s, %s, 'picked_up', %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, now])

        # Notify customer
        _notify(customer_id, 'Order Picked Up',
                f'Your order #{order_id[:8]} has been picked up and is on the way!',
                order_id)

    # Broadcast status change
    broadcast_order_status(order_id, 'picked_up')

    return JsonResponse({'message': 'Order picked up', 'status': 'picked_up'})


# ============================================================================
# PATCH /delivery/orders/<id>/out-for-delivery - Mark en route
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('delivery_partner')
def out_for_delivery(request, order_id):
    """Mark as out for delivery."""
    ok, err, status, customer_id, _ = _verify_assignment(order_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'assigned' in err else 404)
    if status != 'picked_up':
        return JsonResponse({'error': f'Cannot mark out-for-delivery from status: {status}'}, status=400)

    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("UPDATE orders SET status = 'out_for_delivery' WHERE id = %s", [order_id])
            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, changed_at)
                VALUES (%s, %s, 'out_for_delivery', %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, now])

        _notify(customer_id, 'Out for Delivery',
                f'Your order #{order_id[:8]} is out for delivery!', order_id)

    # Broadcast status change
    broadcast_order_status(order_id, 'out_for_delivery')

    return JsonResponse({'message': 'Status updated', 'status': 'out_for_delivery'})


# ============================================================================
# PATCH /delivery/orders/<id>/deliver - Mark delivered
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('delivery_partner')
def deliver_order(request, order_id):
    """Mark order as delivered (final step)."""
    ok, err, status, customer_id, _ = _verify_assignment(order_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'assigned' in err else 404)
    if status not in ('picked_up', 'out_for_delivery'):
        return JsonResponse({'error': f'Cannot deliver order in status: {status}'}, status=400)

    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE orders SET status = 'delivered', delivered_at = %s WHERE id = %s
            """, [now, order_id])

            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, changed_at)
                VALUES (%s, %s, 'delivered', %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, now])

            # For COD, mark payment as success now
            cursor.execute("""
                UPDATE payments SET status = 'success', paid_at = %s
                WHERE order_id = %s AND method = 'cod' AND status != 'success'
            """, [now, order_id])

        _notify(customer_id, 'Delivered!',
                f'Your order #{order_id[:8]} has been delivered. Enjoy your meal!',
                order_id)

    # Broadcast status change
    broadcast_order_status(order_id, 'delivered')

    # Send delivery confirmation email asynchronously
    try:
        from core.Tasks.order_tasks import send_order_delivered_async
        send_order_delivered_async.delay(order_id)
    except Exception:
        pass  # Email failure shouldn't block delivery confirmation

    return JsonResponse({'message': 'Order delivered successfully', 'status': 'delivered'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('delivery/orders/<str:order_id>/pickup', pickup_order, name='delivery-pickup'),
    path('delivery/orders/<str:order_id>/out-for-delivery', out_for_delivery, name='delivery-out'),
    path('delivery/orders/<str:order_id>/deliver', deliver_order, name='delivery-deliver'),
]