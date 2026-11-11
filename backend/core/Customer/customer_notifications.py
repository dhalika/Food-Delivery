"""
Customer notifications - list, mark read.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role


# ============================================================================
# GET /customer/notifications
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('customer')
def list_notifications(request):
    """List customer's notifications."""
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
                'id': r[0], 'title': r[1], 'message': r[2],
                'type': r[3], 'reference_id': r[4], 'is_read': bool(r[5]),
                'created_at': r[6].isoformat() if r[6] else None,
            }
            for r in cursor.fetchall()
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
# PATCH /customer/notifications/<id>/read
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('customer')
def mark_read(request, notif_id):
    """Mark a single notification as read."""
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE notifications SET is_read = TRUE
            WHERE id = %s AND user_id = %s
        """, [notif_id, request.user_id])

    return JsonResponse({'message': 'Marked as read'})


# ============================================================================
# PATCH /customer/notifications/read-all
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('customer')
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
    path('customer/notifications', list_notifications, name='customer-notifications'),
    path('customer/notifications/<str:notif_id>/read', mark_read, name='customer-notif-read'),
    path('customer/notifications/read-all', mark_all_read, name='customer-notif-read-all'),
]