"""
Browse restaurants - list, nearby, filter, search (with Redis caching).
"""
from math import radians, cos, sin, asin, sqrt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from core.Cache.cache_service import cache_get, cache_set
from core.Cache.cache_keys import (
    RESTAURANT_LIST, RESTAURANT_DETAIL, RESTAURANT_NEARBY,
    TTL_RESTAURANT_LIST, TTL_RESTAURANT_DETAIL, TTL_NEARBY,
    make_key,
)


def haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two lat/lng points."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


# ============================================================================
# GET /restaurants - List restaurants (with filters)
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def list_restaurants(request):
    """List all active, verified restaurants."""
    city = request.GET.get('city')
    cuisine_type = request.GET.get('cuisine_type')
    search = request.GET.get('search', '').strip()
    min_rating = request.GET.get('min_rating')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))

    # Only cache the plain unfiltered list (page 1)
    is_cacheable = not any([city, cuisine_type, search, min_rating]) and page == 1 and limit == 20

    if is_cacheable:
        cached = cache_get(RESTAURANT_LIST)
        if cached:
            return JsonResponse(cached)

    offset = (page - 1) * limit
    where = ['is_active = TRUE', 'is_verified = TRUE']
    params = []

    if city:
        where.append('city = %s')
        params.append(city)
    if cuisine_type:
        where.append('cuisine_type LIKE %s')
        params.append(f'%{cuisine_type}%')
    if search:
        where.append('(name LIKE %s OR cuisine_type LIKE %s)')
        params.extend([f'%{search}%', f'%{search}%'])
    if min_rating:
        where.append('avg_rating >= %s')
        params.append(float(min_rating))

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM restaurants WHERE {' AND '.join(where)}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, name, cuisine_type, city, logo_url, banner_url,
                   avg_rating, total_reviews, avg_delivery_time, min_order_value
            FROM restaurants
            WHERE {' AND '.join(where)}
            ORDER BY avg_rating DESC, total_reviews DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        restaurants = [
            {
                'id': r[0], 'name': r[1], 'cuisine_type': r[2], 'city': r[3],
                'logo_url': r[4], 'banner_url': r[5],
                'avg_rating': float(r[6]) if r[6] else 0,
                'total_reviews': r[7],
                'avg_delivery_time': r[8],
                'min_order_value': float(r[9]),
            }
            for r in cursor.fetchall()
        ]

    result = {'total': total, 'page': page, 'restaurants': restaurants}

    # Cache if cacheable
    if is_cacheable:
        cache_set(RESTAURANT_LIST, result, ttl=TTL_RESTAURANT_LIST)

    return JsonResponse(result)


# ============================================================================
# GET /restaurants/nearby?lat=&lng=&radius= - Nearby restaurants
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def nearby_restaurants(request):
    """Nearby restaurants using haversine formula (cached)."""
    try:
        user_lat = float(request.GET['lat'])
        user_lng = float(request.GET['lng'])
        radius_km = float(request.GET.get('radius', 5))
    except (KeyError, ValueError):
        return JsonResponse({'error': 'lat and lng required as float'}, status=400)

    # Cache by rounded coordinates (2 decimals = ~1.1 km precision)
    cache_key = make_key(
        RESTAURANT_NEARBY,
        lat=round(user_lat, 2),
        lng=round(user_lng, 2),
        radius=radius_km,
    )

    cached = cache_get(cache_key)
    if cached:
        return JsonResponse(cached)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, cuisine_type, city, logo_url,
                   avg_rating, total_reviews, avg_delivery_time, min_order_value,
                   lat, lng
            FROM restaurants
            WHERE is_active = TRUE AND is_verified = TRUE
        """)
        all_restaurants = cursor.fetchall()

    nearby = []
    for r in all_restaurants:
        distance = haversine(user_lat, user_lng, float(r[9]), float(r[10]))
        if distance <= radius_km:
            nearby.append({
                'id': r[0], 'name': r[1], 'cuisine_type': r[2], 'city': r[3],
                'logo_url': r[4],
                'avg_rating': float(r[5]) if r[5] else 0,
                'total_reviews': r[6],
                'avg_delivery_time': r[7],
                'min_order_value': float(r[8]),
                'distance_km': round(distance, 2),
            })

    nearby.sort(key=lambda x: x['distance_km'])
    result = {'count': len(nearby), 'restaurants': nearby}

    cache_set(cache_key, result, ttl=TTL_NEARBY)
    return JsonResponse(result)


# ============================================================================
# GET /restaurants/<id> - Restaurant details (cached)
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def get_restaurant(request, restaurant_id):
    """Get restaurant full details for customer."""
    cache_key = make_key(RESTAURANT_DETAIL, restaurant_id=restaurant_id)
    cached = cache_get(cache_key)
    if cached:
        return JsonResponse(cached)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, description, cuisine_type, phone, email,
                   logo_url, banner_url, address, city, pincode, lat, lng,
                   avg_rating, total_reviews, avg_delivery_time, min_order_value,
                   is_active
            FROM restaurants
            WHERE id = %s AND is_verified = TRUE
        """, [restaurant_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)

    result = {
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
    }

    cache_set(cache_key, result, ttl=TTL_RESTAURANT_DETAIL)
    return JsonResponse(result)


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurants', list_restaurants, name='restaurants-list'),
    path('restaurants/nearby', nearby_restaurants, name='restaurants-nearby'),
    path('restaurants/<str:restaurant_id>', get_restaurant, name='restaurant-detail'),
]