"""
Restaurant menu - view full menu with categories grouped (cached).
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from core.Cache.cache_service import cache_get, cache_set
from core.Cache.cache_keys import RESTAURANT_MENU, TTL_MENU, make_key


# ============================================================================
# GET /restaurants/<id>/menu - Full menu grouped by category (cached)
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def get_full_menu(request, restaurant_id):
    """Get restaurant menu grouped by category."""
    cache_key = make_key(RESTAURANT_MENU, restaurant_id=restaurant_id)
    cached = cache_get(cache_key)
    if cached:
        return JsonResponse(cached)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, is_active FROM restaurants
            WHERE id = %s AND is_verified = TRUE
        """, [restaurant_id])
        rest = cursor.fetchone()
        if not rest:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)

        cursor.execute("""
            SELECT id, name, sort_order
            FROM categories
            WHERE restaurant_id = %s AND is_active = TRUE
            ORDER BY sort_order, name
        """, [restaurant_id])
        categories = cursor.fetchall()

        cursor.execute("""
            SELECT id, category_id, name, description, price, image_url,
                   is_veg, is_available, preparation_time
            FROM menu_items
            WHERE restaurant_id = %s
            ORDER BY name
        """, [restaurant_id])
        items = cursor.fetchall()

    items_by_cat = {}
    uncategorized = []
    for item in items:
        item_data = {
            'id': item[0],
            'name': item[2],
            'description': item[3],
            'price': float(item[4]),
            'image_url': item[5],
            'is_veg': bool(item[6]),
            'is_available': bool(item[7]),
            'preparation_time': item[8],
        }
        if item[1]:
            items_by_cat.setdefault(item[1], []).append(item_data)
        else:
            uncategorized.append(item_data)

    menu = []
    for cat in categories:
        menu.append({
            'category_id': cat[0],
            'category_name': cat[1],
            'items': items_by_cat.get(cat[0], []),
        })

    if uncategorized:
        menu.append({
            'category_id': None,
            'category_name': 'Other',
            'items': uncategorized,
        })

    result = {
        'restaurant': {
            'id': rest[0],
            'name': rest[1],
            'is_active': bool(rest[2]),
        },
        'menu': menu,
    }

    cache_set(cache_key, result, ttl=TTL_MENU)
    return JsonResponse(result)


# ============================================================================
# GET /menu-items/<id> - Single menu item
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def get_menu_item(request, item_id):
    """Get a single menu item."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT mi.id, mi.name, mi.description, mi.price, mi.image_url,
                   mi.is_veg, mi.is_available, mi.preparation_time,
                   mi.restaurant_id, r.name
            FROM menu_items mi
            JOIN restaurants r ON r.id = mi.restaurant_id
            WHERE mi.id = %s
        """, [item_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Menu item not found'}, status=404)

    return JsonResponse({
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'price': float(row[3]),
        'image_url': row[4],
        'is_veg': bool(row[5]),
        'is_available': bool(row[6]),
        'preparation_time': row[7],
        'restaurant_id': row[8],
        'restaurant_name': row[9],
    })


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurants/<str:restaurant_id>/menu', get_full_menu, name='restaurant-menu'),
    path('menu-items/<str:item_id>', get_menu_item, name='menu-item-detail'),
]