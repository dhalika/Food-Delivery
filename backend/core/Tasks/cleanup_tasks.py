"""
Celery cleanup tasks - old notifications, stale data.
"""
from celery import shared_task
from datetime import timedelta
import logging

logger = logging.getLogger('core')


@shared_task
def cleanup_old_read_notifications():
    """
    Delete read notifications older than 30 days.
    Run daily at 3 AM.
    """
    from django.utils import timezone
    from django.db import connection

    cutoff = timezone.now() - timedelta(days=30)
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM notifications
            WHERE is_read = TRUE AND created_at < %s
        """, [cutoff])
        deleted = cursor.rowcount

    logger.info(f'Cleaned up {deleted} old read notifications')
    return deleted


@shared_task
def cleanup_old_delivery_locations():
    """
    Delete delivery location records for orders delivered > 24 hours ago.
    Run every 6 hours.
    """
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE dl FROM delivery_locations dl
            JOIN orders o ON o.id = dl.order_id
            WHERE o.status = 'delivered'
                AND o.delivered_at < DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        deleted = cursor.rowcount

    logger.info(f'Cleaned up {deleted} old delivery location records')
    return deleted


@shared_task
def cleanup_abandoned_carts():
    """
    Clear carts that haven't been updated in 7 days.
    Run daily.
    """
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM cart_items
            WHERE cart_id IN (
                SELECT id FROM carts
                WHERE updated_at < DATE_SUB(NOW(), INTERVAL 7 DAY)
            )
        """)
        deleted_items = cursor.rowcount

        cursor.execute("""
            UPDATE carts SET restaurant_id = NULL
            WHERE updated_at < DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)

    logger.info(f'Cleaned up {deleted_items} abandoned cart items')
    return deleted_items