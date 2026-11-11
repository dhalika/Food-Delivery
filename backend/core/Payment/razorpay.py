"""
Razorpay payment integration.
"""
import json
import uuid
import hmac
import hashlib
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from auth.guards import require_role


def _get_razorpay_client():
    """Get Razorpay client instance."""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ============================================================================
# POST /payments/create-order - Create Razorpay order
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def create_razorpay_order(request):
    """
    Create a Razorpay order for a placed order.
    Body: { "order_id": "..." }
    Returns razorpay_order_id for frontend to open checkout.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    order_id = data.get('order_id')
    if not order_id:
        return JsonResponse({'error': 'order_id required'}, status=400)

    with connection.cursor() as cursor:
        # Verify order ownership
        cursor.execute("""
            SELECT final_amount, payment_method, status
            FROM orders
            WHERE id = %s AND customer_id = %s
        """, [order_id, request.user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Order not found'}, status=404)

        final_amount, payment_method, order_status = row

        if payment_method != 'razorpay':
            return JsonResponse({'error': 'Order uses COD, not Razorpay'}, status=400)

        if order_status == 'cancelled':
            return JsonResponse({'error': 'Order was cancelled'}, status=400)

        # Check if payment already exists
        cursor.execute("""
            SELECT id, razorpay_order_id, status FROM payments WHERE order_id = %s
        """, [order_id])
        payment_row = cursor.fetchone()

        if payment_row and payment_row[2] == 'success':
            return JsonResponse({'error': 'Payment already completed'}, status=400)

    # Create Razorpay order
    client = _get_razorpay_client()
    amount_in_paise = int(float(final_amount) * 100)

    try:
        rzp_order = client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': str(order_id),
            'notes': {
                'order_id': str(order_id),
                'customer_id': str(request.user_id),
            },
        })
    except Exception as e:
        return JsonResponse({'error': f'Razorpay error: {str(e)}'}, status=500)

    # Update payment record
    with connection.cursor() as cursor:
        if payment_row:
            cursor.execute("""
                UPDATE payments SET razorpay_order_id = %s, status = 'pending'
                WHERE id = %s
            """, [rzp_order['id'], payment_row[0]])
        else:
            cursor.execute("""
                INSERT INTO payments (id, order_id, method, amount, razorpay_order_id, status)
                VALUES (%s, %s, 'razorpay', %s, %s, 'pending')
            """, [str(uuid.uuid4()), order_id, final_amount, rzp_order['id']])

    return JsonResponse({
        'razorpay_order_id': rzp_order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': amount_in_paise,
        'currency': 'INR',
        'order_id': order_id,
    })


# ============================================================================
# POST /payments/verify - Verify payment signature
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def verify_payment(request):
    """
    Verify Razorpay payment signature after frontend checkout success.
    Body: {
        "razorpay_order_id": "...",
        "razorpay_payment_id": "...",
        "razorpay_signature": "..."
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    rzp_order_id = data.get('razorpay_order_id')
    rzp_payment_id = data.get('razorpay_payment_id')
    rzp_signature = data.get('razorpay_signature')

    if not all([rzp_order_id, rzp_payment_id, rzp_signature]):
        return JsonResponse({'error': 'All razorpay_* fields required'}, status=400)

    # Verify signature
    message = f"{rzp_order_id}|{rzp_payment_id}"
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, rzp_signature):
        # Mark payment as failed
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE payments SET status = 'failed'
                WHERE razorpay_order_id = %s
            """, [rzp_order_id])

        return JsonResponse({'error': 'Invalid signature. Payment verification failed'}, status=400)

    # Update payment and order
    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            # Get payment record
            cursor.execute("""
                SELECT order_id FROM payments WHERE razorpay_order_id = %s
            """, [rzp_order_id])
            row = cursor.fetchone()
            if not row:
                return JsonResponse({'error': 'Payment record not found'}, status=404)

            order_id = row[0]

            # Update payment
            cursor.execute("""
                UPDATE payments SET
                    razorpay_payment_id = %s,
                    razorpay_signature = %s,
                    status = 'success',
                    paid_at = %s
                WHERE razorpay_order_id = %s
            """, [rzp_payment_id, rzp_signature, now, rzp_order_id])

            # Verify order still exists and belongs to user
            cursor.execute("""
                SELECT customer_id, restaurant_id FROM orders WHERE id = %s
            """, [order_id])
            order_row = cursor.fetchone()
            if order_row and order_row[0] == request.user_id:
                # Notify restaurant owner that payment is confirmed
                cursor.execute("SELECT owner_id FROM restaurants WHERE id = %s", [order_row[1]])
                owner = cursor.fetchone()
                if owner:
                    cursor.execute("""
                        INSERT INTO notifications (id, user_id, title, message, type, reference_id)
                        VALUES (%s, %s, %s, %s, 'order_update', %s)
                    """, [
                        str(uuid.uuid4()), owner[0], 'Payment Received',
                        f'Payment confirmed for order #{order_id[:8]}.', order_id,
                    ])

    return JsonResponse({
        'status': 'success',
        'message': 'Payment verified successfully',
        'order_id': order_id,
        'payment_id': rzp_payment_id,
    })


# ============================================================================
# POST /payments/mark-failed - Mark payment as failed (client calls on cancel)
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def mark_payment_failed(request):
    """Mark payment as failed (user closed checkout or payment failed)."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    rzp_order_id = data.get('razorpay_order_id')
    order_id = data.get('order_id')

    if not rzp_order_id and not order_id:
        return JsonResponse({'error': 'razorpay_order_id or order_id required'}, status=400)

    with connection.cursor() as cursor:
        if rzp_order_id:
            cursor.execute("""
                UPDATE payments SET status = 'failed'
                WHERE razorpay_order_id = %s AND status = 'pending'
            """, [rzp_order_id])
        else:
            cursor.execute("""
                UPDATE payments SET status = 'failed'
                WHERE order_id = %s AND status = 'pending'
            """, [order_id])

    return JsonResponse({'message': 'Payment marked as failed'})


# ============================================================================
# GET /payments/<order_id>/status - Check payment status
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def payment_status(request, order_id):
    """Check payment status for an order."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.id, p.method, p.amount, p.status, p.razorpay_order_id,
                   p.razorpay_payment_id, p.paid_at, p.created_at
            FROM payments p
            JOIN orders o ON o.id = p.order_id
            WHERE p.order_id = %s AND o.customer_id = %s
        """, [order_id, request.user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Payment not found'}, status=404)

    return JsonResponse({
        'payment_id': row[0],
        'method': row[1],
        'amount': float(row[2]),
        'status': row[3],
        'razorpay_order_id': row[4],
        'razorpay_payment_id': row[5],
        'paid_at': row[6].isoformat() if row[6] else None,
        'created_at': row[7].isoformat() if row[7] else None,
    })


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('payments/create-order', create_razorpay_order, name='payment-create'),
    path('payments/verify', verify_payment, name='payment-verify'),
    path('payments/mark-failed', mark_payment_failed, name='payment-mark-failed'),
    path('payments/<str:order_id>/status', payment_status, name='payment-status'),
]