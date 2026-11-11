"""
Shopping cart - add, update, remove, clear, view.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role


def _get_or_create_cart(customer_id):
    """Get existing cart or create new one."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM carts WHERE customer_id = %s", [customer_id])
        row = cursor.fetchone()
        if row:
            return row[0]

        cart_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO carts (id, customer_id) VALUES (%s, %s)
        """, [cart_id, customer_id])
        return cart_id


# ============================================================================
# GET /cart - Get current cart
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def get_cart(request):
    """Get current user's cart with items and totals."""
    cart_id = _get_or_create_cart(request.user_id)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.id, c.restaurant_id, r.name, r.logo_url, r.min_order_value, r.avg_delivery_time
            FROM carts c
            LEFT JOIN restaurants r ON r.id = c.restaurant_id
            WHERE c.id = %s
        """, [cart_id])
        cart = cursor.fetchone()

        cursor.execute("""
            SELECT ci.id, ci.menu_item_id, ci.item_name, ci.item_price, ci.quantity,
                   mi.image_url, mi.is_available
            FROM cart_items ci
            LEFT JOIN menu_items mi ON mi.id = ci.menu_item_id
            WHERE ci.cart_id = %s
        """, [cart_id])

        items = []
        subtotal = 0
        for row in cursor.fetchall():
            qty = row[4]
            price = float(row[3])
            item_total = price * qty
            subtotal += item_total
            items.append({
                'id': row[0],
                'menu_item_id': row[1],
                'name': row[2],
                'price': price,
                'quantity': qty,
                'subtotal': item_total,
                'image_url': row[5],
                'is_available': bool(row[6]) if row[6] is not None else True,
            })

    return JsonResponse({
        'cart_id': cart[0],
        'restaurant': {
            'id': cart[1],
            'name': cart[2],
            'logo_url': cart[3],
            'min_order_value': float(cart[4]) if cart[4] else 0,
            'avg_delivery_time': cart[5],
        } if cart[1] else None,
        'items': items,
        'item_count': len(items),
        'subtotal': round(subtotal, 2),
    })


# ============================================================================
# POST /cart/add - Add item to cart
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def add_to_cart(request):
    """Add menu item to cart."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    menu_item_id = data.get('menu_item_id')
    quantity = int(data.get('quantity', 1))

    if not menu_item_id:
        return JsonResponse({'error': 'menu_item_id required'}, status=400)
    if quantity < 1:
        return JsonResponse({'error': 'quantity must be >= 1'}, status=400)

    # Fetch menu item
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, restaurant_id, name, price, is_available
            FROM menu_items WHERE id = %s
        """, [menu_item_id])
        item = cursor.fetchone()

        if not item:
            return JsonResponse({'error': 'Menu item not found'}, status=404)
        if not item[4]:
            return JsonResponse({'error': 'Item not available'}, status=400)

    cart_id = _get_or_create_cart(request.user_id)

    with connection.cursor() as cursor:
        # Get current cart restaurant
        cursor.execute("SELECT restaurant_id FROM carts WHERE id = %s", [cart_id])
        current_rest = cursor.fetchone()[0]

        # If cart has items from different restaurant, clear it
        if current_rest and current_rest != item[1]:
            cursor.execute("DELETE FROM cart_items WHERE cart_id = %s", [cart_id])

        # Update cart's restaurant
        cursor.execute("""
            UPDATE carts SET restaurant_id = %s WHERE id = %s
        """, [item[1], cart_id])

        # Check if item already in cart
        cursor.execute("""
            SELECT id, quantity FROM cart_items
            WHERE cart_id = %s AND menu_item_id = %s
        """, [cart_id, menu_item_id])
        existing = cursor.fetchone()

        if existing:
            new_qty = existing[1] + quantity
            cursor.execute("""
                UPDATE cart_items SET quantity = %s WHERE id = %s
            """, [new_qty, existing[0]])
        else:
            cursor.execute("""
                INSERT INTO cart_items (id, cart_id, menu_item_id, item_name, item_price, quantity)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [str(uuid.uuid4()), cart_id, menu_item_id, item[2], item[3], quantity])

    return JsonResponse({'message': 'Item added to cart'}, status=201)


# ============================================================================
# PUT /cart/items/<id> - Update cart item quantity
# ============================================================================
@csrf_exempt
@require_http_methods(['PUT'])
@require_role('customer')
def update_cart_item(request, item_id):
    """Update quantity of a cart item."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    quantity = int(data.get('quantity', 0))
    if quantity < 1:
        return JsonResponse({'error': 'quantity must be >= 1'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ci.id FROM cart_items ci
            JOIN carts c ON c.id = ci.cart_id
            WHERE ci.id = %s AND c.customer_id = %s
        """, [item_id, request.user_id])
        if not cursor.fetchone():
            return JsonResponse({'error': 'Cart item not found'}, status=404)

        cursor.execute("UPDATE cart_items SET quantity = %s WHERE id = %s",
                       [quantity, item_id])

    return JsonResponse({'message': 'Quantity updated', 'quantity': quantity})


# ============================================================================
# DELETE /cart/items/<id> - Remove item from cart
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_role('customer')
def remove_cart_item(request, item_id):
    """Remove an item from cart."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ci.id, ci.cart_id FROM cart_items ci
            JOIN carts c ON c.id = ci.cart_id
            WHERE ci.id = %s AND c.customer_id = %s
        """, [item_id, request.user_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Cart item not found'}, status=404)

        cursor.execute("DELETE FROM cart_items WHERE id = %s", [item_id])

        # If cart is now empty, unset restaurant
        cursor.execute("SELECT COUNT(*) FROM cart_items WHERE cart_id = %s", [row[1]])
        if cursor.fetchone()[0] == 0:
            cursor.execute("UPDATE carts SET restaurant_id = NULL WHERE id = %s", [row[1]])

    return JsonResponse({'message': 'Item removed'})


# ============================================================================
# DELETE /cart/clear - Clear entire cart
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_role('customer')
def clear_cart(request):
    """Clear all items from cart."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM carts WHERE customer_id = %s", [request.user_id])
        row = cursor.fetchone()
        if row:
            cursor.execute("DELETE FROM cart_items WHERE cart_id = %s", [row[0]])
            cursor.execute("UPDATE carts SET restaurant_id = NULL WHERE id = %s", [row[0]])

    return JsonResponse({'message': 'Cart cleared'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('cart', get_cart, name='cart-get'),
    path('cart/add', add_to_cart, name='cart-add'),
    path('cart/items/<str:item_id>/update', update_cart_item, name='cart-update'),
    path('cart/items/<str:item_id>/remove', remove_cart_item, name='cart-remove'),
    path('cart/clear', clear_cart, name='cart-clear'),
]