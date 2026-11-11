"""
Central notification service - create, list, mark read.
Used by all modules to send in-app notifications.
"""
import uuid
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_auth


VALID_TYPES = {'order_update', 'promotion', 'system'}


# ============================================================================
# CORE HELPER - used by other modules
# ============================================================================
def create_notification(user_id, title, message, notification_type='order_update', reference_id=None):
    """Create an in-app notification for a user."""
    if notification_type not in VALID_TYPES:
        notification_type = 'system'

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO notifications (id, user_id, title, message, type, reference_id, is_read)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
        """, [
            str(uuid.uuid4()), user_id, title, message,
            notification_type, reference_id,
        ])


def broadcast_notification(user_ids, title, message, notification_type='system', reference_id=None):
    """Send same notification to multiple users at once."""
    if not user_ids:
        return
    if notification_type not in VALID_TYPES:
        notification_type = 'system'

    rows = [
        (str(uuid.uuid4()), uid, title, message, notification_type, reference_id, False)
        for uid in user_ids
    ]
    with connection.cursor() as cursor:
        cursor.executemany("""
            INSERT INTO notifications (id, user_id, title, message, type, reference_id, is_read)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, rows)


# ============================================================================
# GET /notifications - List my notifications
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_auth
def list_notifications(request):
    """List notifications for current user."""
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    notification_type = request.GET.get('type')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 50))
    offset = (page - 1) * limit

    where = ['user_id = %s']
    params = [request.user_id]

    if unread_only:
        where.append('is_read = FALSE')
    if notification_type:
        where.append('type = %s')
        params.append(notification_type)

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM notifications WHERE {' AND '.join(where)}", params)
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE", [request.user_id])
        unread_count = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, title, message, type, reference_id, is_read, created_at
            FROM notifications
            WHERE {' AND '.join(where)}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        notifications = [
            {
                'id': r[0], 'title': r[1], 'message': r[2],
                'type': r[3], 'reference_id': r[4],
                'is_read': bool(r[5]),
                'created_at': r[6].isoformat() if r[6] else None,
            }
            for r in cursor.fetchall()
        ]

    return JsonResponse({
        'total': total,
        'unread_count': unread_count,
        'page': page,
        'notifications': notifications,
    })


# ============================================================================
# GET /notifications/unread-count
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_auth
def unread_count(request):
    """Quick count of unread notifications."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM notifications
            WHERE user_id = %s AND is_read = FALSE
        """, [request.user_id])
        count = cursor.fetchone()[0]

    return JsonResponse({'unread_count': count})


# ============================================================================
# PATCH /notifications/<id>/read
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_auth
def mark_read(request, notif_id):
    """Mark a notification as read."""
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE notifications SET is_read = TRUE
            WHERE id = %s AND user_id = %s
        """, [notif_id, request.user_id])
        if cursor.rowcount == 0:
            return JsonResponse({'error': 'Notification not found'}, status=404)

    return JsonResponse({'message': 'Marked as read'})


# ============================================================================
# PATCH /notifications/read-all
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_auth
def mark_all_read(request):
    """Mark all notifications as read."""
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE notifications SET is_read = TRUE
            WHERE user_id = %s AND is_read = FALSE
        """, [request.user_id])
        updated = cursor.rowcount

    return JsonResponse({'message': f'{updated} notifications marked as read'})


# ============================================================================
# DELETE /notifications/<id>/delete
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_auth
def delete_notification(request, notif_id):
    """Delete a notification."""
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM notifications WHERE id = %s AND user_id = %s
        """, [notif_id, request.user_id])
        if cursor.rowcount == 0:
            return JsonResponse({'error': 'Notification not found'}, status=404)

    return JsonResponse({'message': 'Deleted'})


# ============================================================================
# DELETE /notifications/clear-read
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_auth
def clear_read(request):
    """Delete all read notifications."""
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM notifications
            WHERE user_id = %s AND is_read = TRUE
        """, [request.user_id])
        deleted = cursor.rowcount

    return JsonResponse({'message': f'{deleted} notifications deleted'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('notifications', list_notifications, name='notifications-list'),
    path('notifications/unread-count', unread_count, name='notifications-unread-count'),
    path('notifications/<str:notif_id>/read', mark_read, name='notifications-mark-read'),
    path('notifications/read-all', mark_all_read, name='notifications-read-all'),
    path('notifications/<str:notif_id>/delete', delete_notification, name='notifications-delete'),
    path('notifications/clear-read', clear_read, name='notifications-clear-read'),
]