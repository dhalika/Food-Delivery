"""
Admin restaurant management - verify, list, activate/deactivate.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_admin
from core.Cache.cache_invalidation import invalidate_restaurant


# ============================================================================
# GET /admin/restaurants - List all restaurants with filters
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def list_restaurants(request):
    """List restaurants with filters."""
    is_verified = request.GET.get('is_verified')
    is_active = request.GET.get('is_active')
    city = request.GET.get('city')
    cuisine_type = request.GET.get('cuisine_type')
    search = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit

    where_clauses = []
    params = []

    if is_verified is not None:
        where_clauses.append('r.is_verified = %s')
        params.append(is_verified.lower() == 'true')

    if is_active is not None:
        where_clauses.append('r.is_active = %s')
        params.append(is_active.lower() == 'true')

    if city:
        where_clauses.append('r.city = %s')
        params.append(city)

    if cuisine_type:
        where_clauses.append('r.cuisine_type LIKE %s')
        params.append(f'%{cuisine_type}%')

    if search:
        where_clauses.append('(r.name LIKE %s OR r.city LIKE %s)')
        params.extend([f'%{search}%', f'%{search}%'])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM restaurants r {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT
                r.id, r.name, r.cuisine_type, r.city, r.phone,
                r.avg_rating, r.total_reviews, r.is_active, r.is_verified,
                r.created_at, u.name as owner_name, u.email as owner_email
            FROM restaurants r
            LEFT JOIN users u ON u.id = r.owner_id
            {where_sql}
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        restaurants = [
            {
                'id': row[0],
                'name': row[1],
                'cuisine_type': row[2],
                'city': row[3],
                'phone': row[4],
                'avg_rating': float(row[5]) if row[5] else 0,
                'total_reviews': row[6],
                'is_active': bool(row[7]),
                'is_verified': bool(row[8]),
                'created_at': row[9].isoformat() if row[9] else None,
                'owner_name': row[10],
                'owner_email': row[11],
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({
        'total': total,
        'page': page,
        'limit': limit,
        'restaurants': restaurants,
    })


# ============================================================================
# GET /admin/restaurants/<id> - Get restaurant full details
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def get_restaurant_details(request, restaurant_id):
    """Get full details of a restaurant with owner info and stats."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                r.id, r.name, r.description, r.cuisine_type, r.phone, r.email,
                r.logo_url, r.banner_url, r.address, r.city, r.pincode,
                r.lat, r.lng, r.avg_rating, r.total_reviews, r.avg_delivery_time,
                r.min_order_value, r.is_active, r.is_verified,
                r.created_at, r.updated_at,
                u.id as owner_id, u.name as owner_name, u.email as owner_email, u.phone as owner_phone
            FROM restaurants r
            LEFT JOIN users u ON u.id = r.owner_id
            WHERE r.id = %s
        """, [restaurant_id])

        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders WHERE restaurant_id = %s AND status = 'delivered'
        """, [restaurant_id])
        stats = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) FROM menu_items WHERE restaurant_id = %s
        """, [restaurant_id])
        menu_count = cursor.fetchone()[0]

    return JsonResponse({
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'cuisine_type': row[3],
        'phone': row[4],
        'email': row[5],
        'logo_url': row[6],
        'banner_url': row[7],
        'address': row[8],
        'city': row[9],
        'pincode': row[10],
        'lat': float(row[11]) if row[11] else None,
        'lng': float(row[12]) if row[12] else None,
        'avg_rating': float(row[13]) if row[13] else 0,
        'total_reviews': row[14],
        'avg_delivery_time': row[15],
        'min_order_value': float(row[16]),
        'is_active': bool(row[17]),
        'is_verified': bool(row[18]),
        'created_at': row[19].isoformat() if row[19] else None,
        'updated_at': row[20].isoformat() if row[20] else None,
        'owner': {
            'id': row[21],
            'name': row[22],
            'email': row[23],
            'phone': row[24],
        },
        'stats': {
            'total_orders': stats[0],
            'total_revenue': float(stats[1]),
            'menu_items_count': menu_count,
        },
    })


# ============================================================================
# PATCH /admin/restaurants/<id>/verify - Verify or unverify a restaurant
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_admin
def toggle_verify_restaurant(request, restaurant_id):
    """Verify or unverify a restaurant."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT is_verified FROM restaurants WHERE id = %s", [restaurant_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)

        new_status = not bool(row[0])
        cursor.execute(
            "UPDATE restaurants SET is_verified = %s WHERE id = %s",
            [new_status, restaurant_id]
        )

    invalidate_restaurant(restaurant_id)

    return JsonResponse({
        'restaurant_id': restaurant_id,
        'is_verified': new_status,
        'message': f"Restaurant {'verified' if new_status else 'unverified'} successfully"
    })


# ============================================================================
# PATCH /admin/restaurants/<id>/toggle-active - Enable/disable a restaurant
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_admin
def toggle_active_restaurant(request, restaurant_id):
    """Admin can force enable/disable a restaurant."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT is_active FROM restaurants WHERE id = %s", [restaurant_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)

        new_status = not bool(row[0])
        cursor.execute(
            "UPDATE restaurants SET is_active = %s WHERE id = %s",
            [new_status, restaurant_id]
        )

    invalidate_restaurant(restaurant_id)

    return JsonResponse({
        'restaurant_id': restaurant_id,
        'is_active': new_status,
    })


# ============================================================================
# DELETE /admin/restaurants/<id> - Delete a restaurant
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_admin
def delete_restaurant(request, restaurant_id):
    """Permanently delete a restaurant (cascades menu, orders)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM restaurants WHERE id = %s", [restaurant_id])
        if not cursor.fetchone():
            return JsonResponse({'error': 'Restaurant not found'}, status=404)

        cursor.execute("DELETE FROM restaurants WHERE id = %s", [restaurant_id])

    invalidate_restaurant(restaurant_id)

    return JsonResponse({'message': 'Restaurant deleted successfully'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('admin/restaurants', list_restaurants, name='admin-restaurants-list'),
    path('admin/restaurants/<str:restaurant_id>', get_restaurant_details, name='admin-restaurant-detail'),
    path('admin/restaurants/<str:restaurant_id>/verify', toggle_verify_restaurant, name='admin-restaurant-verify'),
    path('admin/restaurants/<str:restaurant_id>/toggle-active', toggle_active_restaurant, name='admin-restaurant-toggle'),
    path('admin/restaurants/<str:restaurant_id>/delete', delete_restaurant, name='admin-restaurant-delete'),
]