"""
Group Order feature — friends share cart, host pays, split shown.
"""
import json
import uuid
import random
import string
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta

from auth.guards import require_role, require_auth


def generate_share_code():
    """Generate unique 6-char share code like 'HKFG5X'."""
    chars = string.ascii_uppercase + string.digits
    return 'HK' + ''.join(random.choices(chars, k=4))


def _broadcast_group_update(group_id):
    """Broadcast update to all group WebSocket subscribers."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'group_{group_id}',
                {'type': 'group_update', 'group_id': str(group_id)}
            )
    except Exception:
        pass


# ============================================================================
# POST /group-orders/create - Host creates group
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def create_group_order(request):
    """Create a new group order for a restaurant."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    restaurant_id = data.get('restaurant_id')
    if not restaurant_id:
        return JsonResponse({'error': 'restaurant_id required'}, status=400)

    # Verify restaurant exists and active
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name FROM restaurants
            WHERE id = %s AND is_active = TRUE AND is_verified = TRUE
        """, [restaurant_id])
        rest = cursor.fetchone()
        if not rest:
            return JsonResponse({'error': 'Restaurant not available'}, status=404)

        # Generate unique code
        for _ in range(5):
            code = generate_share_code()
            cursor.execute("SELECT id FROM group_orders WHERE share_code = %s", [code])
            if not cursor.fetchone():
                break

        group_id = str(uuid.uuid4())
        expires = timezone.now() + timedelta(hours=2)

        cursor.execute("""
            INSERT INTO group_orders (id, share_code, host_id, restaurant_id, status, expires_at)
            VALUES (%s, %s, %s, %s, 'open', %s)
        """, [group_id, code, request.user_id, restaurant_id, expires])

    return JsonResponse({
        'group_id': group_id,
        'share_code': code,
        'restaurant_name': rest[1],
        'expires_at': expires.isoformat(),
        'share_url': f'/customer/group/{code}',
    }, status=201)


# ============================================================================
# GET /group-orders/<code> - Get group details by code
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def get_group_by_code(request, code):
    """Get group order details by share code."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT g.id, g.share_code, g.host_id, g.restaurant_id, g.status,
                   g.created_at, g.expires_at,
                   r.name, r.cuisine_type, r.logo_url, r.min_order_value,
                   u.name as host_name
            FROM group_orders g
            JOIN restaurants r ON r.id = g.restaurant_id
            JOIN users u ON u.id = g.host_id
            WHERE g.share_code = %s
        """, [code.upper()])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Group order not found'}, status=404)

        if row[4] in ('placed', 'cancelled'):
            return JsonResponse({'error': f'Group is {row[4]}'}, status=400)

        group_id = row[0]

        # Get all items grouped by user
        cursor.execute("""
            SELECT id, user_id, user_name, menu_item_id, item_name,
                   item_price, quantity, added_at
            FROM group_order_items
            WHERE group_order_id = %s
            ORDER BY added_at
        """, [group_id])

        items = []
        members = {}
        grand_total = Decimal('0')

        for r in cursor.fetchall():
            subtotal = Decimal(str(r[5])) * r[6]
            grand_total += subtotal
            items.append({
                'id': r[0],
                'user_id': r[1],
                'user_name': r[2],
                'menu_item_id': r[3],
                'name': r[4],
                'price': float(r[5]),
                'quantity': r[6],
                'subtotal': float(subtotal),
                'is_mine': r[1] == request.user_id,
            })
            if r[1] not in members:
                members[r[1]] = {'user_id': r[1], 'name': r[2], 'subtotal': 0}
            members[r[1]]['subtotal'] += float(subtotal)

    return JsonResponse({
        'group_id': row[0],
        'share_code': row[1],
        'is_host': row[2] == request.user_id,
        'status': row[4],
        'restaurant': {
            'id': row[3],
            'name': row[7],
            'cuisine_type': row[8],
            'logo_url': row[9],
            'min_order_value': float(row[10]),
        },
        'host_name': row[11],
        'created_at': row[5].isoformat() if row[5] else None,
        'expires_at': row[6].isoformat() if row[6] else None,
        'items': items,
        'members': list(members.values()),
        'subtotal': float(grand_total),
        'member_count': len(members),
    })


# ============================================================================
# POST /group-orders/<id>/add-item - Add item to group
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def add_item_to_group(request, group_id):
    """Add menu item to group order."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    menu_item_id = data.get('menu_item_id')
    quantity = int(data.get('quantity', 1))

    with connection.cursor() as cursor:
        # Check group exists and open
        cursor.execute("""
            SELECT status, restaurant_id FROM group_orders WHERE id = %s
        """, [group_id])
        group = cursor.fetchone()
        if not group:
            return JsonResponse({'error': 'Group not found'}, status=404)
        if group[0] != 'open':
            return JsonResponse({'error': f'Group is {group[0]}'}, status=400)

        # Get menu item
        cursor.execute("""
            SELECT name, price, is_available, restaurant_id
            FROM menu_items WHERE id = %s
        """, [menu_item_id])
        item = cursor.fetchone()
        if not item or not item[2]:
            return JsonResponse({'error': 'Item unavailable'}, status=404)
        if item[3] != group[1]:
            return JsonResponse({'error': 'Item not from this restaurant'}, status=400)

        # Get user name
        cursor.execute("SELECT name FROM users WHERE id = %s", [request.user_id])
        user_name = cursor.fetchone()[0]

        # Insert item
        item_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO group_order_items (id, group_order_id, user_id, user_name,
                                          menu_item_id, item_name, item_price, quantity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, [item_id, group_id, request.user_id, user_name, menu_item_id,
              item[0], item[1], quantity])

    _broadcast_group_update(group_id)
    return JsonResponse({'id': item_id, 'message': 'Added to group'}, status=201)


# ============================================================================
# DELETE /group-orders/items/<id> - Remove own item
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_role('customer')
def remove_group_item(request, item_id):
    """Remove own item from group (only own items)."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT user_id, group_order_id FROM group_order_items WHERE id = %s
        """, [item_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Item not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': "Can't remove others' items"}, status=403)

        group_id = row[1]
        cursor.execute("DELETE FROM group_order_items WHERE id = %s", [item_id])

    _broadcast_group_update(group_id)
    return JsonResponse({'message': 'Removed'})


# ============================================================================
# POST /group-orders/<id>/finalize - Host checks out
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def finalize_group_order(request, group_id):
    """Host finalizes group order - places actual order."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    delivery_address_id = data.get('delivery_address_id')
    payment_method = data.get('payment_method', 'cod')

    if not delivery_address_id:
        return JsonResponse({'error': 'delivery_address_id required'}, status=400)

    with connection.cursor() as cursor:
        # Verify host
        cursor.execute("""
            SELECT host_id, restaurant_id, status FROM group_orders WHERE id = %s
        """, [group_id])
        g = cursor.fetchone()
        if not g:
            return JsonResponse({'error': 'Group not found'}, status=404)
        if g[0] != request.user_id:
            return JsonResponse({'error': 'Only host can finalize'}, status=403)
        if g[2] != 'open':
            return JsonResponse({'error': 'Group already finalized'}, status=400)

        # Verify address
        cursor.execute("""
            SELECT id FROM addresses WHERE id = %s AND user_id = %s
        """, [delivery_address_id, request.user_id])
        if not cursor.fetchone():
            return JsonResponse({'error': 'Invalid address'}, status=400)

        # Get all items
        cursor.execute("""
            SELECT menu_item_id, item_name, item_price, quantity, user_id, user_name
            FROM group_order_items WHERE group_order_id = %s
        """, [group_id])
        items = cursor.fetchall()

        if not items:
            return JsonResponse({'error': 'Group cart is empty'}, status=400)

        # Calculate split
        splits = {}
        item_total = Decimal('0')
        for it in items:
            subtotal = Decimal(str(it[2])) * it[3]
            item_total += subtotal
            uid = it[4]
            if uid not in splits:
                splits[uid] = {'name': it[5], 'amount': Decimal('0')}
            splits[uid]['amount'] += subtotal

        delivery_fee = Decimal('30.00')
        tax = item_total * Decimal('0.05')
        final_amount = item_total + delivery_fee + tax

        # Create order
        order_id = str(uuid.uuid4())
        now = timezone.now()

        with transaction.atomic():
            cursor.execute("""
                INSERT INTO orders (
                    id, customer_id, restaurant_id, delivery_address_id,
                    status, item_total, discount_amount, delivery_fee, tax_amount,
                    final_amount, payment_method, placed_at,
                    special_instructions
                ) VALUES (%s, %s, %s, %s, 'placed', %s, 0, %s, %s, %s, %s, %s, %s)
            """, [
                order_id, request.user_id, g[1], delivery_address_id,
                item_total, delivery_fee, tax, final_amount,
                payment_method, now, '👥 GROUP ORDER',
            ])

            # Order items
            for it in items:
                cursor.execute("""
                    INSERT INTO order_items (id, order_id, menu_item_id, item_name,
                                            item_price, quantity, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [str(uuid.uuid4()), order_id, it[0], f"{it[1]} ({it[5]})",
                      it[2], it[3], Decimal(str(it[2])) * it[3]])

            # Status history
            cursor.execute("""
                INSERT INTO order_status_history (id, order_id, status, changed_by, changed_at)
                VALUES (%s, %s, 'placed', %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, now])

            # Payment
            cursor.execute("""
                INSERT INTO payments (id, order_id, method, amount, status)
                VALUES (%s, %s, %s, %s, %s)
            """, [str(uuid.uuid4()), order_id, payment_method, final_amount,
                  'pending' if payment_method == 'razorpay' else 'success'])

            # Lock group + link order
            cursor.execute("""
                UPDATE group_orders SET status = 'placed',
                                       final_order_id = %s,
                                       delivery_address_id = %s
                WHERE id = %s
            """, [order_id, delivery_address_id, group_id])

            # Notify restaurant
            cursor.execute("SELECT owner_id FROM restaurants WHERE id = %s", [g[1]])
            owner_id = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO notifications (id, user_id, title, message, type, reference_id)
                VALUES (%s, %s, '👥 Group Order!', %s, 'order_update', %s)
            """, [str(uuid.uuid4()), owner_id,
                  f'New GROUP order #{order_id[:8]} - {len(splits)} members',
                  order_id])

            # Notify all group members
            for uid, info in splits.items():
                if uid != request.user_id:
                    cursor.execute("""
                        INSERT INTO notifications (id, user_id, title, message, type, reference_id)
                        VALUES (%s, %s, 'Group Order Placed!', %s, 'order_update', %s)
                    """, [str(uuid.uuid4()), uid,
                          f'Your group order for ₹{info["amount"]} is placed. Pay the host!',
                          order_id])

    _broadcast_group_update(group_id)

    # Build split response
    split_list = [
        {'user_id': uid, 'name': info['name'], 'amount': round(float(info['amount']), 2)}
        for uid, info in splits.items()
    ]

    return JsonResponse({
        'order_id': order_id,
        'status': 'placed',
        'item_total': float(item_total),
        'delivery_fee': float(delivery_fee),
        'tax': round(float(tax), 2),
        'final_amount': round(float(final_amount), 2),
        'splits': split_list,
        'member_count': len(splits),
    }, status=201)


# ============================================================================
# POST /group-orders/<id>/cancel - Host cancels group
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def cancel_group_order(request, group_id):
    """Host cancels open group."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT host_id, status FROM group_orders WHERE id = %s", [group_id])
        g = cursor.fetchone()
        if not g:
            return JsonResponse({'error': 'Group not found'}, status=404)
        if g[0] != request.user_id:
            return JsonResponse({'error': 'Only host can cancel'}, status=403)
        if g[1] != 'open':
            return JsonResponse({'error': 'Cannot cancel'}, status=400)

        cursor.execute("UPDATE group_orders SET status = 'cancelled' WHERE id = %s", [group_id])

    _broadcast_group_update(group_id)
    return JsonResponse({'message': 'Group cancelled'})


# ============================================================================
# GET /group-orders/my - List my active group orders
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def my_group_orders(request):
    """List groups user is part of (host or member)."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT g.id, g.share_code, g.status, g.created_at,
                   r.name as restaurant_name,
                   (g.host_id = %s) as is_host,
                   (SELECT COUNT(DISTINCT user_id) FROM group_order_items WHERE group_order_id = g.id) as member_count
            FROM group_orders g
            JOIN restaurants r ON r.id = g.restaurant_id
            WHERE g.host_id = %s
               OR g.id IN (SELECT group_order_id FROM group_order_items WHERE user_id = %s)
            ORDER BY g.created_at DESC
            LIMIT 20
        """, [request.user_id, request.user_id, request.user_id])

        groups = [
            {
                'id': r[0],
                'share_code': r[1],
                'status': r[2],
                'created_at': r[3].isoformat() if r[3] else None,
                'restaurant_name': r[4],
                'is_host': bool(r[5]),
                'member_count': r[6],
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({'groups': groups})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('group-orders/create', create_group_order, name='group-create'),
    path('group-orders/my', my_group_orders, name='group-my'),
    path('group-orders/code/<str:code>', get_group_by_code, name='group-by-code'),
    path('group-orders/<str:group_id>/add-item', add_item_to_group, name='group-add-item'),
    path('group-orders/items/<str:item_id>/remove', remove_group_item, name='group-remove-item'),
    path('group-orders/<str:group_id>/finalize', finalize_group_order, name='group-finalize'),
    path('group-orders/<str:group_id>/cancel', cancel_group_order, name='group-cancel'),
]