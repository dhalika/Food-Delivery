"""
Restaurant timings - set day-wise opening hours.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role
from core.Cache.cache_service import cache_delete
from core.Cache.cache_keys import RESTAURANT_TIMINGS, make_key


def _verify_ownership(restaurant_id, user_id):
    """Check if user owns the restaurant."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT owner_id FROM restaurants WHERE id = %s", [restaurant_id])
        row = cursor.fetchone()
        if not row:
            return False, 'Restaurant not found'
        if row[0] != user_id:
            return False, 'Not your restaurant'
    return True, None


# ============================================================================
# POST /restaurants/<id>/timings - Set/update timings (bulk)
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('restaurant_owner')
def set_timings(request, restaurant_id):
    """Set all 7 days of timings in one call."""
    ok, err = _verify_ownership(restaurant_id, request.user_id)
    if not ok:
        return JsonResponse({'error': err}, status=403 if 'yours' in err else 404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    timings = data.get('timings', [])
    if not timings:
        return JsonResponse({'error': 'timings array is required'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM restaurant_timings WHERE restaurant_id = %s", [restaurant_id])

        for t in timings:
            day = t.get('day')
            opening = t.get('opening')
            closing = t.get('closing')
            is_closed = t.get('is_closed', False)

            if day is None or day < 0 or day > 6:
                return JsonResponse({'error': f'Invalid day: {day} (must be 0-6)'}, status=400)
            if not is_closed and (not opening or not closing):
                return JsonResponse({'error': f'opening and closing required for day {day}'}, status=400)

            cursor.execute("""
                INSERT INTO restaurant_timings
                (id, restaurant_id, day_of_week, opening_time, closing_time, is_closed)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [str(uuid.uuid4()), restaurant_id, day,
                  opening or '00:00:00', closing or '00:00:00', is_closed])

    # Invalidate timings cache
    cache_delete(make_key(RESTAURANT_TIMINGS, restaurant_id=restaurant_id))

    return JsonResponse({'message': 'Timings saved successfully'})


# ============================================================================
# GET /restaurants/<id>/timings - Get timings
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def get_timings(request, restaurant_id):
    """Get restaurant timings (public)."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT day_of_week, opening_time, closing_time, is_closed
            FROM restaurant_timings
            WHERE restaurant_id = %s
            ORDER BY day_of_week
        """, [restaurant_id])

        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        timings = [
            {
                'day': row[0],
                'day_name': day_names[row[0]],
                'opening_time': str(row[1]) if row[1] else None,
                'closing_time': str(row[2]) if row[2] else None,
                'is_closed': bool(row[3]),
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({'restaurant_id': restaurant_id, 'timings': timings})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurants/<str:restaurant_id>/timings', get_timings, name='restaurant-timings-get'),
    path('restaurants/<str:restaurant_id>/timings/set', set_timings, name='restaurant-timings-set'),
]