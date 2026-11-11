"""
Menu management - categories, menu items, availability toggle.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection, IntegrityError

from auth.guards import require_role
from core.Cache.cache_invalidation import invalidate_menu


def _verify_restaurant_ownership(restaurant_id, user_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT owner_id FROM restaurants WHERE id = %s", [restaurant_id])
        row = cursor.fetchone()
        if not row:
            return False, 'Restaurant not found'
        if row[0] != user_id:
            return False, 'Not your restaurant'
    return True, None


def _verify_menu_item_ownership(menu_item_id, user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT r.owner_id, mi.restaurant_id
            FROM menu_items mi
            JOIN restaurants r ON r.id = mi.restaurant_id
            WHERE mi.id = %s
        """, [menu_item_id])
        row = cursor.fetchone()
        if not row:
            return False, 'Menu item not found', None
        if row[0] != user_id:
            return False, 'Not your menu item', None
    return True, None, row[1]


# ============================================================================
# POST /restaurants/<id>/categories - Create category
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('restaurant_owner')
def create_category(request, restaurant_id):
    """Create a menu category."""
    ok, err = _verify_restaurant_ownership(restaurant_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    sort_order = data.get('sort_order', 0)

    if not name:
        return JsonResponse({'error': 'Category name is required'}, status=400)

    category_id = str(uuid.uuid4())
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO categories (id, restaurant_id, name, sort_order, is_active)
                VALUES (%s, %s, %s, %s, TRUE)
            """, [category_id, restaurant_id, name, sort_order])
    except IntegrityError:
        return JsonResponse({'error': 'Category name already exists for this restaurant'}, status=409)

    # Invalidate menu cache
    invalidate_menu(restaurant_id)

    return JsonResponse({'id': category_id, 'name': name}, status=201)


# ============================================================================
# GET /restaurants/<id>/categories - List categories
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def list_categories(request, restaurant_id):
    """List all categories for a restaurant (public)."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, sort_order, is_active
            FROM categories
            WHERE restaurant_id = %s
            ORDER BY sort_order, name
        """, [restaurant_id])
        categories = [
            {'id': r[0], 'name': r[1], 'sort_order': r[2], 'is_active': bool(r[3])}
            for r in cursor.fetchall()
        ]
    return JsonResponse({'categories': categories})


# ============================================================================
# DELETE /categories/<id> - Delete category
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_role('restaurant_owner')
def delete_category(request, category_id):
    """Delete a category (menu items become uncategorized)."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT r.owner_id, c.restaurant_id FROM categories c
            JOIN restaurants r ON r.id = c.restaurant_id
            WHERE c.id = %s
        """, [category_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Category not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': 'Not your category'}, status=403)

        restaurant_id = row[1]
        cursor.execute("DELETE FROM categories WHERE id = %s", [category_id])

    # Invalidate menu cache
    invalidate_menu(restaurant_id)

    return JsonResponse({'message': 'Category deleted'})


# ============================================================================
# POST /restaurants/<id>/menu-items - Create menu item
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('restaurant_owner')
def create_menu_item(request, restaurant_id):
    """Add a new menu item."""
    ok, err = _verify_restaurant_ownership(restaurant_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    price = data.get('price')

    if not name:
        return JsonResponse({'error': 'name is required'}, status=400)
    if price is None or float(price) <= 0:
        return JsonResponse({'error': 'price must be > 0'}, status=400)

    item_id = str(uuid.uuid4())
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO menu_items (
                id, restaurant_id, category_id, name, description, price,
                image_url, is_veg, is_available, preparation_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            item_id, restaurant_id, data.get('category_id'), name,
            data.get('description'), price, data.get('image_url'),
            data.get('is_veg', True), data.get('is_available', True),
            data.get('preparation_time'),
        ])

    # Invalidate menu cache
    invalidate_menu(restaurant_id)

    return JsonResponse({'id': item_id, 'message': 'Menu item added'}, status=201)


# ============================================================================
# GET /restaurants/<id>/menu-items - List menu items
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def list_menu_items(request, restaurant_id):
    """List all menu items for a restaurant (public)."""
    category_id = request.GET.get('category_id')
    is_veg = request.GET.get('is_veg')

    where = ['mi.restaurant_id = %s']
    params = [restaurant_id]

    if category_id:
        where.append('mi.category_id = %s')
        params.append(category_id)
    if is_veg is not None:
        where.append('mi.is_veg = %s')
        params.append(is_veg.lower() == 'true')

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT mi.id, mi.name, mi.description, mi.price, mi.image_url,
                   mi.is_veg, mi.is_available, mi.preparation_time,
                   c.id, c.name
            FROM menu_items mi
            LEFT JOIN categories c ON c.id = mi.category_id
            WHERE {' AND '.join(where)}
            ORDER BY c.sort_order, mi.name
        """, params)

        items = [
            {
                'id': r[0], 'name': r[1], 'description': r[2],
                'price': float(r[3]), 'image_url': r[4],
                'is_veg': bool(r[5]), 'is_available': bool(r[6]),
                'preparation_time': r[7],
                'category': {'id': r[8], 'name': r[9]} if r[8] else None,
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({'items': items})


# ============================================================================
# PUT /menu-items/<id> - Update menu item
# ============================================================================
@csrf_exempt
@require_http_methods(['PUT'])
@require_role('restaurant_owner')
def update_menu_item(request, item_id):
    """Update a menu item."""
    ok, err, restaurant_id = _verify_menu_item_ownership(item_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    allowed = {'category_id', 'name', 'description', 'price', 'image_url',
               'is_veg', 'is_available', 'preparation_time'}
    updates = []
    params = []
    for field in allowed:
        if field in data:
            updates.append(f'{field} = %s')
            params.append(data[field])

    if not updates:
        return JsonResponse({'error': 'No fields to update'}, status=400)

    params.append(item_id)
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE menu_items SET {', '.join(updates)} WHERE id = %s", params)

    # Invalidate menu cache
    invalidate_menu(restaurant_id)

    return JsonResponse({'message': 'Menu item updated'})


# ============================================================================
# PATCH /menu-items/<id>/toggle - Toggle availability
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('restaurant_owner')
def toggle_availability(request, item_id):
    """Toggle menu item availability."""
    ok, err, restaurant_id = _verify_menu_item_ownership(item_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)

    with connection.cursor() as cursor:
        cursor.execute("SELECT is_available FROM menu_items WHERE id = %s", [item_id])
        current = bool(cursor.fetchone()[0])
        new_status = not current
        cursor.execute("UPDATE menu_items SET is_available = %s WHERE id = %s",
                       [new_status, item_id])

    # Invalidate menu cache
    invalidate_menu(restaurant_id)

    return JsonResponse({'id': item_id, 'is_available': new_status})


# ============================================================================
# DELETE /menu-items/<id> - Delete menu item
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_role('restaurant_owner')
def delete_menu_item(request, item_id):
    """Delete a menu item."""
    ok, err, restaurant_id = _verify_menu_item_ownership(item_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM menu_items WHERE id = %s", [item_id])

    # Invalidate menu cache
    invalidate_menu(restaurant_id)

    return JsonResponse({'message': 'Menu item deleted'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurants/<str:restaurant_id>/categories', list_categories, name='categories-list'),
    path('restaurants/<str:restaurant_id>/categories/create', create_category, name='category-create'),
    path('categories/<str:category_id>/delete', delete_category, name='category-delete'),
    path('restaurants/<str:restaurant_id>/menu-items', list_menu_items, name='menu-items-list'),
    path('restaurants/<str:restaurant_id>/menu-items/create', create_menu_item, name='menu-item-create'),
    path('menu-items/<str:item_id>/update', update_menu_item, name='menu-item-update'),
    path('menu-items/<str:item_id>/toggle', toggle_availability, name='menu-item-toggle'),
    path('menu-items/<str:item_id>/delete', delete_menu_item, name='menu-item-delete'),
]