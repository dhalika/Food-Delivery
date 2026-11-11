"""
Admin user management - list, block/unblock, view details, delete.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection

from auth.guards import require_admin


# ============================================================================
# GET /admin/users - List all users with filters
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def list_users(request):
    """
    List users with optional filters.
    Query params: role, is_active, search (name/email/phone), page, limit
    """
    role = request.GET.get('role')
    is_active = request.GET.get('is_active')
    search = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit

    where_clauses = []
    params = []

    if role:
        where_clauses.append('role = %s')
        params.append(role)

    if is_active is not None:
        where_clauses.append('is_active = %s')
        params.append(is_active.lower() == 'true')

    if search:
        where_clauses.append('(name LIKE %s OR email LIKE %s OR phone LIKE %s)')
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    with connection.cursor() as cursor:
        # Count total
        cursor.execute(f"SELECT COUNT(*) FROM users {where_sql}", params)
        total = cursor.fetchone()[0]

        # Get users
        cursor.execute(f"""
            SELECT id, name, email, phone, role, is_active, is_available, created_at
            FROM users
            {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        users = [
            {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'role': row[4],
                'is_active': bool(row[5]),
                'is_available': bool(row[6]),
                'created_at': row[7].isoformat() if row[7] else None,
            }
            for row in cursor.fetchall()
        ]

    return JsonResponse({
        'total': total,
        'page': page,
        'limit': limit,
        'users': users,
    })


# ============================================================================
# GET /admin/users/<user_id> - Get user details with stats
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def get_user_details(request, user_id):
    """Get full details of a user including their activity stats."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, email, phone, role, avatar_url,
                   is_active, is_available, created_at, updated_at
            FROM users WHERE id = %s
        """, [user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'User not found'}, status=404)

        user = {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'role': row[4],
            'avatar_url': row[5],
            'is_active': bool(row[6]),
            'is_available': bool(row[7]),
            'created_at': row[8].isoformat() if row[8] else None,
            'updated_at': row[9].isoformat() if row[9] else None,
        }

        # Role-specific stats
        if user['role'] == 'customer':
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
                FROM orders WHERE customer_id = %s
            """, [user_id])
            stats = cursor.fetchone()
            user['stats'] = {
                'total_orders': stats[0],
                'total_spent': float(stats[1]),
            }

        elif user['role'] == 'restaurant_owner':
            cursor.execute("""
                SELECT COUNT(*) FROM restaurants WHERE owner_id = %s
            """, [user_id])
            user['stats'] = {
                'total_restaurants': cursor.fetchone()[0],
            }

        elif user['role'] == 'delivery_partner':
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
                FROM orders WHERE delivery_partner_id = %s AND status = 'delivered'
            """, [user_id])
            stats = cursor.fetchone()
            user['stats'] = {
                'total_deliveries': stats[0],
                'total_revenue_handled': float(stats[1]),
            }

    return JsonResponse(user)


# ============================================================================
# PATCH /admin/users/<user_id>/block - Block or unblock a user
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_admin
def toggle_block_user(request, user_id):
    """Toggle is_active for a user (block/unblock)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT is_active FROM users WHERE id = %s", [user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'User not found'}, status=404)

        new_status = not bool(row[0])
        cursor.execute(
            "UPDATE users SET is_active = %s WHERE id = %s",
            [new_status, user_id]
        )

    return JsonResponse({
        'user_id': user_id,
        'is_active': new_status,
        'message': f"User {'unblocked' if new_status else 'blocked'} successfully"
    })


# ============================================================================
# DELETE /admin/users/<user_id> - Permanently delete a user
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_admin
def delete_user(request, user_id):
    """Permanently delete a user."""
    # Prevent self-deletion
    if user_id == request.user_id:
        return JsonResponse({'error': 'Cannot delete your own account'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("SELECT role FROM users WHERE id = %s", [user_id])
        row = cursor.fetchone()

        if not row:
            return JsonResponse({'error': 'User not found'}, status=404)

        cursor.execute("DELETE FROM users WHERE id = %s", [user_id])

    return JsonResponse({'message': 'User deleted successfully'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('admin/users', list_users, name='admin-users-list'),
    path('admin/users/<str:user_id>', get_user_details, name='admin-user-detail'),
    path('admin/users/<str:user_id>/block', toggle_block_user, name='admin-user-block'),
    path('admin/users/<str:user_id>/delete', delete_user, name='admin-user-delete'),
]