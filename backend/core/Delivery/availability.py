"""
Delivery partner availability - toggle online/offline.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_role


# ============================================================================
# PATCH /delivery/availability - Toggle online/offline
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_role('delivery_partner')
def toggle_availability(request):
    """Toggle delivery partner's online/offline status."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT is_available FROM users WHERE id = %s", [request.user_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'User not found'}, status=404)

        new_status = not bool(row[0])
        cursor.execute(
            "UPDATE users SET is_available = %s WHERE id = %s",
            [new_status, request.user_id]
        )

    return JsonResponse({
        'is_available': new_status,
        'message': f"You are now {'online' if new_status else 'offline'}",
    })


# ============================================================================
# GET /delivery/availability - Current status
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_role('delivery_partner')
def get_availability(request):
    """Get current availability status."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT is_available FROM users WHERE id = %s", [request.user_id])
        row = cursor.fetchone()

    return JsonResponse({'is_available': bool(row[0]) if row else False})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('delivery/availability', get_availability, name='delivery-availability-get'),
    path('delivery/availability/toggle', toggle_availability, name='delivery-availability-toggle'),
]