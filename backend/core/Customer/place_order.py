"""
Place order - convert cart to order with atomic transaction.
"""
import json
import uuid
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection, transaction
from django.utils import timezone

from auth.guards import require_role


DELIVERY_FEE = Decimal('30.00')
TAX_RATE = Decimal('0.05')  # 5% GST


# ============================================================================
# POST /orders/place - Place an order
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def place_order(request):
    """
    Place order from cart.
    Body: {
        "delivery_address_id": "...",
        "payment_method": "razorpay" | "cod",
        "coupon_code": "SAVE20" (optional),
        "special_instructions": "..." (optional)
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    delivery_address_id = data.get('delivery_address_id')
    payment_method = data.get('payment_method', '').lower()
    coupon_code = data.get('coupon_code', '').strip().upper()
    special_instructions = data.get('special_instructions', '')

    # Validation
    if not delivery_address_id:
        return JsonResponse({'error': 'delivery_address_id required'}, status=400)
    if payment_method not in ('razorpay', 'cod'):
        return JsonResponse({'error': 'payment_method must be razorpay or cod'}, status=400)

    with connection.cursor() as cursor:
        # Verify address
        cursor.execute("""
            SELECT id FROM addresses WHERE id = %s AND user_id = %s
        """, [delivery_address_id, request.user_id])
        if not cursor.fetchone():
            return JsonResponse({'error': 'Invalid delivery address'}, status=400)

        # Get cart with items
        cursor.execute("""
            SELECT c.id, c.restaurant_id, r.min_order_value, r.is_active, r.avg_delivery_time
            FROM carts c
            JOIN restaurants r ON r.id = c.restaurant_id
            WHERE c.customer_id = %s
        """, [request.user_id])
        cart = cursor.fetchone()

        if not cart:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        if not cart[3]:
            return JsonResponse({'error': 'Restaurant is currently not accepting orders'}, status=400)

        cart_id, restaurant_id, min_order_value, _, est_delivery = cart

        # Get cart items
        cursor.execute("""
            SELECT menu_item_id, item_name, item_price, quantity
            FROM cart_items WHERE cart_id = %s
        """, [cart_id])
        cart_items = cursor.fetchall()

        if not cart_items:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        # Calculate totals
        item_total = sum(Decimal(str(row[2])) * row[3] for row in cart_items)

        if item_total < Decimal(str(min_order_value)):
            return JsonResponse({
                'error': f'Minimum order value is ₹{min_order_value}',
                'current': float(item_total),
            }, status=400)

        # Coupon handling
        discount = Decimal('0.00')
        coupon_id = None
        if coupon_code:
            now = timezone.now()
            cursor.execute("""
                SELECT id, discount_type, discount_value, max_discount,
                       min_order_value, usage_limit, per_user_limit
                FROM coupons
                WHERE code = %s AND is_active = TRUE
                    AND valid_from <= %s AND valid_till >= %s
            """, [coupon_code, now, now])
            coupon = cursor.fetchone()

            if not coupon:
                return JsonResponse({'error': 'Invalid or expired coupon'}, status=400)

            coupon_id = coupon[0]

            # Check limits
            if coupon[5]:
                cursor.execute("SELECT COUNT(*) FROM coupon_usage WHERE coupon_id = %s", [coupon_id])
                if cursor.fetchone()[0] >= coupon[5]:
                    return JsonResponse({'error': 'Coupon usage limit reached'}, status=400)

            cursor.execute("""
                SELECT COUNT(*) FROM coupon_usage WHERE coupon_id = %s AND user_id = %s
            """, [coupon_id, request.user_id])
            if cursor.fetchone()[0] >= coupon[6]:
                return JsonResponse({'error': 'You have already used this coupon'}, status=400)

            if item_total < Decimal(str(coupon[4])):
                return JsonResponse({'error': f'Minimum order for coupon: ₹{coupon[4]}'}, status=400)

            # Calculate discount
            if coupon[1] == 'percentage':
                discount = item_total * Decimal(str(coupon[2])) / 100
                if coupon[3]:
                    discount = min(discount, Decimal(str(coupon[3])))
            else:
                discount = min(Decimal(str(coupon[2])), item_total)

        tax = (item_total - discount) * TAX_RATE
        final_amount = item_total - discount + DELIVERY_FEE + tax

        # Create order atomically
        order_id = str(uuid.uuid4())
        now = timezone.now()

        with transaction.atomic():
            # Insert order
            cursor.execute("""
                INSERT INTO orders (
                    id, customer_id, restaurant_id, delivery_address_id, coupon_id,
                    status, item_total, discount_amount, delivery_fee, tax_amount,
                    final_amount, payment_method, special_instructions,
                    estimated_delivery_time, placed_at
                ) VALUES (%s, %s, %s, %s, %s, 'placed', %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                order_id, request.user_id, restaurant_id, delivery_address_id, coupon_id,
                item_total, discount, DELIVERY_FEE, tax, final_amount,
                payment_method, special_instructions, est_delivery, now,
            ])

            # Insert order items
            for ci in cart_items:
                cursor.execute("""
                    INSERT INTO order_items (id, order_id, menu_item_id, item_name,
                                             item_price, quantity, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    str(uuid.uuid4()), order_id, ci[0], ci[1], ci[2], ci[3],
                    Decimal(str(ci[2])) * ci[3],
                ])

            # Status history
            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, changed_at)
                VALUES (%s, %s, 'placed', %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, now])

            # Record coupon usage
            if coupon_id:
                cursor.execute("""
                    INSERT INTO coupon_usage (id, coupon_id, user_id, order_id)
                    VALUES (%s, %s, %s, %s)
                """, [str(uuid.uuid4()), coupon_id, request.user_id, order_id])

            # Create payment record
            cursor.execute("""
                INSERT INTO payments (id, order_id, method, amount, status)
                VALUES (%s, %s, %s, %s, %s)
            """, [
                str(uuid.uuid4()), order_id, payment_method, final_amount,
                'pending' if payment_method == 'razorpay' else 'success',
            ])

            # Notify restaurant owner
            cursor.execute("SELECT owner_id FROM restaurants WHERE id = %s", [restaurant_id])
            owner_id = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO notifications (id, user_id, title, message, type, reference_id)
                VALUES (%s, %s, %s, %s, 'order_update', %s)
            """, [
                str(uuid.uuid4()), owner_id, 'New Order!',
                f'New order #{order_id[:8]} received.', order_id,
            ])

            # Clear cart
            cursor.execute("DELETE FROM cart_items WHERE cart_id = %s", [cart_id])
            cursor.execute("UPDATE carts SET restaurant_id = NULL WHERE id = %s", [cart_id])

    # Send confirmation email asynchronously (don't block response)
    try:
        from core.Tasks.order_tasks import send_order_confirmation_async
        send_order_confirmation_async.delay(order_id)
    except Exception:
        pass  # Email failure shouldn't block order

    return JsonResponse({
        'order_id': order_id,
        'status': 'placed',
        'item_total': float(item_total),
        'discount': float(discount),
        'delivery_fee': float(DELIVERY_FEE),
        'tax': round(float(tax), 2),
        'final_amount': round(float(final_amount), 2),
        'payment_method': payment_method,
        'next_step': 'proceed_to_payment' if payment_method == 'razorpay' else 'order_confirmed',
    }, status=201)


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('orders/place', place_order, name='order-place'),
]