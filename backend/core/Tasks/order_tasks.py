"""
Celery tasks for orders - async email sending, auto-cancel.
"""
from celery import shared_task
from datetime import timedelta
import logging

logger = logging.getLogger('core')


@shared_task
def send_order_confirmation_async(order_id: str):
    """Send order confirmation email in background."""
    from core.Notification.email_service import send_order_confirmation_email
    try:
        result = send_order_confirmation_email(order_id)
        logger.info(f'Order confirmation email: order={order_id}, sent={result}')
        return result
    except Exception as e:
        logger.error(f'send_order_confirmation_async failed: {e}')
        return False


@shared_task
def send_order_delivered_async(order_id: str):
    """Send delivery confirmation in background."""
    from core.Notification.email_service import send_order_delivered_email
    try:
        return send_order_delivered_email(order_id)
    except Exception as e:
        logger.error(f'send_order_delivered_async failed: {e}')
        return False


@shared_task
def send_order_cancelled_async(order_id: str):
    """Send cancellation email in background."""
    from core.Notification.email_service import send_order_cancelled_email
    try:
        return send_order_cancelled_email(order_id)
    except Exception as e:
        logger.error(f'send_order_cancelled_async failed: {e}')
        return False


@shared_task
def send_welcome_email_async(user_id: str):
    """Send welcome email in background."""
    from core.Notification.email_service import send_welcome_email
    try:
        return send_welcome_email(user_id)
    except Exception as e:
        logger.error(f'send_welcome_email_async failed: {e}')
        return False


@shared_task
def auto_cancel_unaccepted_orders():
    """
    Scheduled task: Cancel orders not accepted within 10 minutes.
    Run every 2 minutes via celery-beat.
    """
    import uuid
    from django.utils import timezone
    from django.db import connection

    cutoff = timezone.now() - timedelta(minutes=10)
    cancelled_count = 0

    with connection.cursor() as cursor:
        # Find stale pending orders
        cursor.execute("""
            SELECT id, customer_id FROM orders
            WHERE status = 'placed' AND placed_at < %s
        """, [cutoff])
        stale_orders = cursor.fetchall()

        now = timezone.now()
        for order_id, customer_id in stale_orders:
            # Cancel
            cursor.execute("""
                UPDATE orders SET
                    status = 'cancelled',
                    cancelled_at = %s,
                    cancel_reason = 'Auto-cancelled: restaurant did not accept within 10 minutes',
                    cancelled_by = 'admin'
                WHERE id = %s
            """, [now, order_id])

            # Log status history
            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, note, changed_at)
                VALUES (%s, %s, 'cancelled', %s, %s)
            """, [
                str(uuid.uuid4()), order_id,
                'Auto-cancelled: not accepted in 10 min', now,
            ])

            # Notify customer
            cursor.execute("""
                INSERT INTO notifications (id, user_id, title, message, type, reference_id)
                VALUES (%s, %s, %s, %s, 'order_update', %s)
            """, [
                str(uuid.uuid4()), customer_id, 'Order Cancelled',
                f'Your order #{order_id[:8]} was auto-cancelled (not accepted by restaurant in time).',
                order_id,
            ])

            # Send cancellation email
            send_order_cancelled_async.delay(order_id)
            cancelled_count += 1

    logger.info(f'auto_cancel_unaccepted_orders: cancelled {cancelled_count} orders')
    return cancelled_count