"""
Admin dashboard - overview stats and revenue reports.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_admin
from core.Cache.cache_service import cache_get, cache_set
from core.Cache.cache_keys import ADMIN_STATS, TTL_ADMIN_STATS


# ============================================================================
# GET /admin/stats - Overview stats (cached)
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def dashboard_stats(request):
    """Get platform-wide statistics."""
    # Check cache first
    cached = cache_get(ADMIN_STATS)
    if cached:
        return JsonResponse(cached)

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(final_amount), 0) FROM orders WHERE status = 'delivered'")
        total_revenue = float(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
        active_users = cursor.fetchone()[0]

        cursor.execute("""
            SELECT role, COUNT(*) FROM users WHERE is_active = TRUE GROUP BY role
        """)
        users_by_role = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT COUNT(*) FROM restaurants WHERE is_active = TRUE AND is_verified = TRUE
        """)
        active_restaurants = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM restaurants WHERE is_verified = FALSE")
        pending_verifications = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM orders
            WHERE placed_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        orders_last_30_days = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(AVG(final_amount), 0) FROM orders WHERE status = 'delivered'
        """)
        avg_order_value = float(cursor.fetchone()[0])

        cursor.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        orders_by_status = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
            FROM orders WHERE DATE(placed_at) = CURDATE()
        """)
        today_row = cursor.fetchone()
        today_orders = today_row[0]
        today_revenue = float(today_row[1])

    result = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'active_users': active_users,
        'users_by_role': users_by_role,
        'active_restaurants': active_restaurants,
        'pending_verifications': pending_verifications,
        'orders_last_30_days': orders_last_30_days,
        'avg_order_value': round(avg_order_value, 2),
        'orders_by_status': orders_by_status,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
    }

    # Cache for 2 minutes
    cache_set(ADMIN_STATS, result, ttl=TTL_ADMIN_STATS)

    return JsonResponse(result)


# ============================================================================
# GET /admin/revenue-report?from=YYYY-MM-DD&to=YYYY-MM-DD
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def revenue_report(request):
    """Get revenue report between date range."""
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')

    if not from_date or not to_date:
        return JsonResponse({'error': 'from and to date params required (YYYY-MM-DD)'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_orders,
                COALESCE(SUM(final_amount), 0) as total_revenue,
                COALESCE(AVG(final_amount), 0) as avg_order_value,
                COALESCE(SUM(discount_amount), 0) as total_discounts,
                COALESCE(SUM(delivery_fee), 0) as total_delivery_fees,
                COALESCE(SUM(tax_amount), 0) as total_tax
            FROM orders
            WHERE status = 'delivered'
                AND DATE(placed_at) BETWEEN %s AND %s
        """, [from_date, to_date])
        row = cursor.fetchone()

        cursor.execute("""
            SELECT
                DATE(placed_at) as order_date,
                COUNT(*) as orders,
                COALESCE(SUM(final_amount), 0) as revenue
            FROM orders
            WHERE status = 'delivered'
                AND DATE(placed_at) BETWEEN %s AND %s
            GROUP BY DATE(placed_at)
            ORDER BY order_date
        """, [from_date, to_date])

        daily = [
            {
                'date': str(r[0]),
                'orders': r[1],
                'revenue': float(r[2]),
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({
        'from': from_date,
        'to': to_date,
        'total_orders': row[0],
        'total_revenue': float(row[1]),
        'avg_order_value': round(float(row[2]), 2),
        'total_discounts': float(row[3]),
        'total_delivery_fees': float(row[4]),
        'total_tax': float(row[5]),
        'daily_breakdown': daily,
    })


# ============================================================================
# GET /admin/top-restaurants - Top-performing restaurants
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def top_restaurants(request):
    """Top restaurants by revenue (last 30 days)."""
    limit = int(request.GET.get('limit', 10))

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                r.id, r.name, r.city, r.avg_rating,
                COUNT(o.id) as total_orders,
                COALESCE(SUM(o.final_amount), 0) as total_revenue
            FROM restaurants r
            LEFT JOIN orders o ON o.restaurant_id = r.id
                AND o.status = 'delivered'
                AND o.placed_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            WHERE r.is_active = TRUE
            GROUP BY r.id, r.name, r.city, r.avg_rating
            ORDER BY total_revenue DESC
            LIMIT %s
        """, [limit])

        results = [
            {
                'restaurant_id': row[0],
                'name': row[1],
                'city': row[2],
                'avg_rating': float(row[3]) if row[3] else 0,
                'total_orders': row[4],
                'total_revenue': float(row[5]),
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({'top_restaurants': results})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('admin/stats', dashboard_stats, name='admin-stats'),
    path('admin/revenue-report', revenue_report, name='admin-revenue-report'),
    path('admin/top-restaurants', top_restaurants, name='admin-top-restaurants'),
]