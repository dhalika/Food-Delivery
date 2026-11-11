"""
Apply coupon - validate and calculate discount.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection
from django.utils import timezone

from auth.guards import require_role


# ============================================================================
# POST /cart/apply-coupon - Apply coupon to cart
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def apply_coupon(request):
    """Validate coupon against user's cart and return discount."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    code = data.get('code', '').strip().upper()
    if not code:
        return JsonResponse({'error': 'Coupon code required'}, status=400)

    now = timezone.now()

    with connection.cursor() as cursor:
        # Get coupon
        cursor.execute("""
            SELECT id, code, discount_type, discount_value, max_discount,
                   min_order_value, usage_limit, per_user_limit, valid_from, valid_till
            FROM coupons
            WHERE code = %s AND is_active = TRUE
                AND valid_from <= %s AND valid_till >= %s
        """, [code, now, now])
        coupon = cursor.fetchone()

        if not coupon:
            return JsonResponse({'error': 'Invalid or expired coupon'}, status=400)

        coupon_id = coupon[0]

        # Check global usage limit
        if coupon[6]:
            cursor.execute("SELECT COUNT(*) FROM coupon_usage WHERE coupon_id = %s", [coupon_id])
            total_used = cursor.fetchone()[0]
            if total_used >= coupon[6]:
                return JsonResponse({'error': 'Coupon usage limit reached'}, status=400)

        # Check per-user limit
        cursor.execute("""
            SELECT COUNT(*) FROM coupon_usage WHERE coupon_id = %s AND user_id = %s
        """, [coupon_id, request.user_id])
        user_used = cursor.fetchone()[0]
        if user_used >= coupon[7]:
            return JsonResponse({'error': 'You have already used this coupon'}, status=400)

        # Get cart total
        cursor.execute("""
            SELECT COALESCE(SUM(ci.item_price * ci.quantity), 0)
            FROM carts c
            LEFT JOIN cart_items ci ON ci.cart_id = c.id
            WHERE c.customer_id = %s
        """, [request.user_id])
        cart_total = float(cursor.fetchone()[0])

        if cart_total == 0:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        # Check min order value
        min_order = float(coupon[5])
        if cart_total < min_order:
            return JsonResponse({
                'error': f'Minimum order value is ₹{min_order}',
                'cart_total': cart_total,
                'needed': round(min_order - cart_total, 2),
            }, status=400)

        # Calculate discount
        discount_type = coupon[2]
        discount_value = float(coupon[3])
        max_discount = float(coupon[4]) if coupon[4] else None

        if discount_type == 'percentage':
            discount = cart_total * discount_value / 100
            if max_discount:
                discount = min(discount, max_discount)
        else:  # flat
            discount = min(discount_value, cart_total)

        return JsonResponse({
            'valid': True,
            'coupon_id': coupon_id,
            'code': coupon[1],
            'cart_total': round(cart_total, 2),
            'discount': round(discount, 2),
            'payable': round(cart_total - discount, 2),
        })


# ============================================================================
# GET /coupons/available - Browse available coupons
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def available_coupons(request):
    """List coupons user can use."""
    now = timezone.now()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, code, description, discount_type, discount_value,
                   max_discount, min_order_value, valid_till
            FROM coupons
            WHERE is_active = TRUE AND valid_from <= %s AND valid_till >= %s
            ORDER BY discount_value DESC
        """, [now, now])

        coupons = [
            {
                'id': r[0],
                'code': r[1],
                'description': r[2],
                'discount_type': r[3],
                'discount_value': float(r[4]),
                'max_discount': float(r[5]) if r[5] else None,
                'min_order_value': float(r[6]),
                'valid_till': r[7].isoformat() if r[7] else None,
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({'coupons': coupons})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('cart/apply-coupon', apply_coupon, name='cart-apply-coupon'),
    path('coupons/available', available_coupons, name='coupons-available'),
]