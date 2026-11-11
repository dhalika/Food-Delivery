"""
Sales dashboard for restaurant owners.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role


# ============================================================================
# GET /restaurant/dashboard - Sales overview
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('restaurant_owner')
def dashboard(request):
    """Owner's sales dashboard — today, week, month."""
    restaurant_id = request.GET.get('restaurant_id')
    if not restaurant_id:
        return JsonResponse({'error': 'restaurant_id query param required'}, status=400)

    # Verify ownership
    with connection.cursor() as cursor:
        cursor.execute("SELECT owner_id FROM restaurants WHERE id = %s", [restaurant_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Restaurant not found'}, status=404)
        if row[0] != request.user_id:
            return JsonResponse({'error': 'Not your restaurant'}, status=403)

        # Today
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders
            WHERE restaurant_id = %s AND DATE(placed_at) = CURDATE()
        """, [restaurant_id])
        today = cursor.fetchone()

        # This week
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders
            WHERE restaurant_id = %s AND placed_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """, [restaurant_id])
        week = cursor.fetchone()

        # This month
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders
            WHERE restaurant_id = %s AND MONTH(placed_at) = MONTH(CURDATE())
                AND YEAR(placed_at) = YEAR(CURDATE())
        """, [restaurant_id])
        month = cursor.fetchone()

        # Delivered only (lifetime revenue)
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders
            WHERE restaurant_id = %s AND status = 'delivered'
        """, [restaurant_id])
        lifetime = cursor.fetchone()

        # Orders by status
        cursor.execute("""
            SELECT status, COUNT(*) FROM orders WHERE restaurant_id = %s GROUP BY status
        """, [restaurant_id])
        by_status = {row[0]: row[1] for row in cursor.fetchall()}

        # Top-selling items (last 30 days)
        cursor.execute("""
            SELECT oi.item_name, SUM(oi.quantity) as total_qty,
                   SUM(oi.subtotal) as revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.restaurant_id = %s
                AND o.placed_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY oi.item_name
            ORDER BY total_qty DESC
            LIMIT 10
        """, [restaurant_id])
        top_items = [
            {'name': r[0], 'quantity_sold': int(r[1]), 'revenue': float(r[2])}
            for r in cursor.fetchall()
        ]

        # Daily revenue last 7 days
        cursor.execute("""
            SELECT DATE(placed_at), COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders
            WHERE restaurant_id = %s AND placed_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(placed_at)
            ORDER BY DATE(placed_at)
        """, [restaurant_id])
        daily = [
            {'date': str(r[0]), 'orders': r[1], 'revenue': float(r[2])}
            for r in cursor.fetchall()
        ]

    return JsonResponse({
        'restaurant_id': restaurant_id,
        'today': {'orders': today[0], 'revenue': float(today[1])},
        'this_week': {'orders': week[0], 'revenue': float(week[1])},
        'this_month': {'orders': month[0], 'revenue': float(month[1])},
        'lifetime': {'orders': lifetime[0], 'revenue': float(lifetime[1])},
        'orders_by_status': by_status,
        'top_selling_items': top_items,
        'daily_revenue_last_7_days': daily,
    })


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurant/dashboard', dashboard, name='restaurant-dashboard'),
]