"""
Notifications for restaurant owners.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role


# ============================================================================
# GET /restaurant/notifications - My notifications
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('restaurant_owner')
def list_notifications(request):
    """List notifications for current restaurant owner."""
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    limit = int(request.GET.get('limit', 50))

    where = ['user_id = %s']
    params = [request.user_id]

    if unread_only:
        where.append('is_read = FALSE')

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT id, title, message, type, reference_id, is_read, created_at
            FROM notifications
            WHERE {' AND '.join(where)}
            ORDER BY created_at DESC
            LIMIT %s
        """, params + [limit])

        notifications = [
            {
                'id': row[0],
                'title': row[1],
                'message': row[2],
                'type': row[3],
                'reference_id': row[4],
                'is_read': bool(row[5]),
                'created_at': row[6].isoformat() if row[6] else None,
            }
            for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE user_id = %s AND is_read = FALSE
        """, [request.user_id])
        unread_count = cursor.fetchone()[0]

    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notifications,
    })


# ============================================================================
# PATCH /restaurant/notifications/<id>/read - Mark as read
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('restaurant_owner')
def mark_read(request, notif_id):
    """Mark a notification as read."""
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE notifications SET is_read = TRUE
            WHERE id = %s AND user_id = %s
        """, [notif_id, request.user_id])

    return JsonResponse({'message': 'Marked as read'})


# ============================================================================
# PATCH /restaurant/notifications/read-all - Mark all as read
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('restaurant_owner')
def mark_all_read(request):
    """Mark all notifications as read."""
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE notifications SET is_read = TRUE
            WHERE user_id = %s AND is_read = FALSE
        """, [request.user_id])

    return JsonResponse({'message': 'All marked as read'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('restaurant/notifications', list_notifications, name='restaurant-notifications'),
    path('restaurant/notifications/<str:notif_id>/read', mark_read, name='restaurant-notif-read'),
    path('restaurant/notifications/read-all', mark_all_read, name='restaurant-notif-read-all'),
]