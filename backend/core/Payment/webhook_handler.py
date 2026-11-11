"""
Razorpay webhook handler - handles server-to-server callbacks.
This runs WITHOUT authentication (webhook endpoint is public).
"""
import json
import uuid
import hmac
import hashlib
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.conf import settings
from django.db import connection
from django.utils import timezone

logger = logging.getLogger('core')


def _verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', settings.RAZORPAY_KEY_SECRET)

    expected = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


# ============================================================================
# POST /payments/webhook - Razorpay webhook endpoint
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
def razorpay_webhook(request):
    """
    Razorpay webhook endpoint.
    Handles: payment.captured, payment.failed, order.paid, refund.processed
    """
    # Verify signature
    signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')
    if not signature:
        logger.warning('Webhook received without signature')
        return JsonResponse({'error': 'Missing signature'}, status=400)

    if not _verify_webhook_signature(request.body, signature):
        logger.warning('Webhook signature verification failed')
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Parse payload
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    event = payload.get('event', '')
    logger.info(f'Webhook received: {event}')

    # Dispatch event
    if event == 'payment.captured':
        return _handle_payment_captured(payload)
    elif event == 'payment.failed':
        return _handle_payment_failed(payload)
    elif event == 'order.paid':
        return _handle_order_paid(payload)
    elif event == 'refund.processed':
        return _handle_refund_processed(payload)
    else:
        logger.info(f'Unhandled webhook event: {event}')
        return JsonResponse({'status': 'ignored', 'event': event})


# ============================================================================
# Event handlers
# ============================================================================
def _handle_payment_captured(payload):
    """Payment successfully captured."""
    payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
    rzp_order_id = payment_entity.get('order_id')
    rzp_payment_id = payment_entity.get('id')
    amount = payment_entity.get('amount', 0) / 100  # Convert paise to rupees

    if not rzp_order_id:
        return JsonResponse({'error': 'order_id missing in payload'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, order_id, status FROM payments WHERE razorpay_order_id = %s
        """, [rzp_order_id])
        row = cursor.fetchone()

        if not row:
            logger.warning(f'Payment not found for razorpay_order_id: {rzp_order_id}')
            return JsonResponse({'status': 'payment_not_found'})

        payment_id, order_id, current_status = row

        if current_status == 'success':
            return JsonResponse({'status': 'already_processed'})

        now = timezone.now()
        cursor.execute("""
            UPDATE payments SET
                razorpay_payment_id = %s,
                status = 'success',
                paid_at = %s
            WHERE id = %s
        """, [rzp_payment_id, now, payment_id])

        # Notify restaurant
        cursor.execute("""
            SELECT r.owner_id FROM orders o
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE o.id = %s
        """, [order_id])
        owner = cursor.fetchone()
        if owner:
            cursor.execute("""
                INSERT INTO notifications (id, user_id, title, message, type, reference_id)
                VALUES (%s, %s, %s, %s, 'order_update', %s)
            """, [
                str(uuid.uuid4()), owner[0], 'Payment Captured',
                f'Payment of ₹{amount} received for order #{order_id[:8]}.',
                order_id,
            ])

    logger.info(f'Payment captured: order_id={order_id}, amount={amount}')
    return JsonResponse({'status': 'success', 'order_id': order_id})


def _handle_payment_failed(payload):
    """Payment failed."""
    payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
    rzp_order_id = payment_entity.get('order_id')
    error_desc = payment_entity.get('error_description', 'Unknown error')

    if not rzp_order_id:
        return JsonResponse({'error': 'order_id missing'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE payments SET status = 'failed'
            WHERE razorpay_order_id = %s
        """, [rzp_order_id])

    logger.info(f'Payment failed: rzp_order_id={rzp_order_id}, reason={error_desc}')
    return JsonResponse({'status': 'failed_recorded'})


def _handle_order_paid(payload):
    """Order fully paid (in case of partial payments)."""
    order_entity = payload.get('payload', {}).get('order', {}).get('entity', {})
    rzp_order_id = order_entity.get('id')

    if not rzp_order_id:
        return JsonResponse({'error': 'order_id missing'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE payments SET status = 'success', paid_at = %s
            WHERE razorpay_order_id = %s AND status != 'success'
        """, [timezone.now(), rzp_order_id])

    logger.info(f'Order paid: rzp_order_id={rzp_order_id}')
    return JsonResponse({'status': 'success'})


def _handle_refund_processed(payload):
    """Refund processed."""
    refund_entity = payload.get('payload', {}).get('refund', {}).get('entity', {})
    rzp_payment_id = refund_entity.get('payment_id')
    amount = refund_entity.get('amount', 0) / 100

    if not rzp_payment_id:
        return JsonResponse({'error': 'payment_id missing'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE payments SET status = 'refunded'
            WHERE razorpay_payment_id = %s
        """, [rzp_payment_id])

        cursor.execute("""
            SELECT order_id FROM payments WHERE razorpay_payment_id = %s
        """, [rzp_payment_id])
        row = cursor.fetchone()
        if row:
            order_id = row[0]
            cursor.execute("""
                SELECT customer_id FROM orders WHERE id = %s
            """, [order_id])
            cust = cursor.fetchone()
            if cust:
                cursor.execute("""
                    INSERT INTO notifications (id, user_id, title, message, type, reference_id)
                    VALUES (%s, %s, %s, %s, 'order_update', %s)
                """, [
                    str(uuid.uuid4()), cust[0], 'Refund Processed',
                    f'₹{amount} has been refunded to your account.', order_id,
                ])

    logger.info(f'Refund processed: rzp_payment_id={rzp_payment_id}, amount={amount}')
    return JsonResponse({'status': 'refund_recorded'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('payments/webhook', razorpay_webhook, name='payment-webhook'),
]