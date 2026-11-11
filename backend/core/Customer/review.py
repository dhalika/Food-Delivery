"""
Reviews - post review for delivered order.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection, IntegrityError

from auth.guards import require_role


# ============================================================================
# POST /orders/<id>/review - Post review
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_role('customer')
def create_review(request, order_id):
    """Review a delivered order."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    rating = data.get('rating')
    comment = data.get('comment', '')

    if not rating or not (1 <= int(rating) <= 5):
        return JsonResponse({'error': 'rating must be 1-5'}, status=400)

    with connection.cursor() as cursor:
        # Verify order is delivered and belongs to customer
        cursor.execute("""
            SELECT restaurant_id, status FROM orders
            WHERE id = %s AND customer_id = %s
        """, [order_id, request.user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'Order not found'}, status=404)
        if row[1] != 'delivered':
            return JsonResponse({'error': 'Can only review delivered orders'}, status=400)

        restaurant_id = row[0]

        # Insert review
        try:
            cursor.execute("""
                INSERT INTO reviews (id, order_id, customer_id, restaurant_id, rating, comment)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [str(uuid.uuid4()), order_id, request.user_id, restaurant_id, rating, comment])
        except IntegrityError:
            return JsonResponse({'error': 'You have already reviewed this order'}, status=409)

        # Update restaurant's avg_rating and total_reviews
        cursor.execute("""
            SELECT AVG(rating), COUNT(*) FROM reviews WHERE restaurant_id = %s
        """, [restaurant_id])
        avg, count = cursor.fetchone()

        cursor.execute("""
            UPDATE restaurants SET avg_rating = %s, total_reviews = %s WHERE id = %s
        """, [round(float(avg), 1), count, restaurant_id])

    return JsonResponse({'message': 'Review submitted successfully'}, status=201)


# ============================================================================
# GET /reviews/me - My reviews
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def my_reviews(request):
    """List my past reviews."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT rv.id, rv.rating, rv.comment, rv.created_at,
                   rv.order_id, r.name as restaurant_name
            FROM reviews rv
            JOIN restaurants r ON r.id = rv.restaurant_id
            WHERE rv.customer_id = %s
            ORDER BY rv.created_at DESC
        """, [request.user_id])

        reviews = [
            {
                'id': r[0],
                'rating': r[1],
                'comment': r[2],
                'created_at': r[3].isoformat() if r[3] else None,
                'order_id': r[4],
                'restaurant_name': r[5],
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({'reviews': reviews})


# ============================================================================
# GET /restaurants/<id>/reviews - Public reviews for restaurant
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
def restaurant_reviews(request, restaurant_id):
    """Public view of a restaurant's reviews."""
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE restaurant_id = %s", [restaurant_id])
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT rv.rating, rv.comment, rv.created_at, c.name
            FROM reviews rv
            JOIN users c ON c.id = rv.customer_id
            WHERE rv.restaurant_id = %s
            ORDER BY rv.created_at DESC
            LIMIT %s OFFSET %s
        """, [restaurant_id, limit, offset])

        reviews = [
            {
                'rating': r[0],
                'comment': r[1],
                'created_at': r[2].isoformat() if r[2] else None,
                'customer_name': r[3],
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({'total': total, 'reviews': reviews})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('orders/<str:order_id>/review', create_review, name='order-review'),
    path('reviews/me', my_reviews, name='my-reviews'),
    path('restaurants/<str:restaurant_id>/reviews', restaurant_reviews, name='restaurant-reviews-public'),
]