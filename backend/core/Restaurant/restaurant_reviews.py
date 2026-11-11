"""
Restaurant reviews - view reviews for owned restaurants.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role


# ============================================================================
# GET /restaurant/<id>/reviews - List reviews
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('restaurant_owner')
def list_my_reviews(request, restaurant_id):
    """Reviews for one of my restaurants."""
    # Verify ownership
    with connection.cursor() as cursor:
        cursor.execute("SELECT owner_id FROM restaurants WHERE id = %s", [restaurant_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': 'Not your restaurant'}, status=403)

        # Overall stats
        cursor.execute("""
            SELECT COUNT(*), COALESCE(AVG(rating), 0),
                   SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END)
            FROM reviews WHERE restaurant_id = %s
        """, [restaurant_id])
        s = cursor.fetchone()

        # Reviews list
        cursor.execute("""
            SELECT r.id, r.rating, r.comment, r.created_at,
                   c.name as customer_name
            FROM reviews r
            JOIN users c ON c.id = r.customer_id
            WHERE r.restaurant_id = %s
            ORDER BY r.created_at DESC
            LIMIT 50
        """, [restaurant_id])

        reviews = [
            {
                'id': row[0],
                'rating': row[1],
                'comment': row[2],
                'created_at': row[3].isoformat() if row[3] else None,
                'customer_name': row[4],
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({
        'stats': {
            'total_reviews': s[0],
            'average_rating': round(float(s[1]), 2),
            'rating_breakdown': {
                '5_star': int(s[2] or 0),
                '4_star': int(s[3] or 0),
                '3_star': int(s[4] or 0),
                '2_star': int(s[5] or 0),
                '1_star': int(s[6] or 0),
            },
        },
        'reviews': reviews,
    })


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurant/<str:restaurant_id>/reviews', list_my_reviews, name='restaurant-reviews'),
]