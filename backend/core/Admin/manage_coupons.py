"""
Admin coupon management - create, list, update, deactivate.
"""
import json
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path
from django.db import connection, IntegrityError

from auth.guards import require_admin
from core.Cache.cache_invalidation import invalidate_coupons


VALID_DISCOUNT_TYPES = {'percentage', 'flat'}


# ============================================================================
# POST /admin/coupons - Create a new coupon
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_admin
def create_coupon(request):
    """Create a new discount coupon."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    code = data.get('code', '').strip().upper()
    discount_type = data.get('discount_type', '').strip().lower()
    discount_value = data.get('discount_value')
    valid_from = data.get('valid_from')
    valid_till = data.get('valid_till')
    description = data.get('description', '')
    max_discount = data.get('max_discount')
    min_order_value = data.get('min_order_value', 0)
    usage_limit = data.get('usage_limit')
    per_user_limit = data.get('per_user_limit', 1)

    if not code or len(code) < 3:
        return JsonResponse({'error': 'Coupon code is required (min 3 chars)'}, status=400)
    if discount_type not in VALID_DISCOUNT_TYPES:
        return JsonResponse(
            {'error': f'discount_type must be one of: {", ".join(VALID_DISCOUNT_TYPES)}'},
            status=400
        )
    if not discount_value or float(discount_value) <= 0:
        return JsonResponse({'error': 'discount_value must be > 0'}, status=400)
    if discount_type == 'percentage' and float(discount_value) > 100:
        return JsonResponse({'error': 'Percentage discount cannot exceed 100'}, status=400)
    if not valid_from or not valid_till:
        return JsonResponse({'error': 'valid_from and valid_till are required'}, status=400)

    coupon_id = str(uuid.uuid4())

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO coupons (id, code, description, discount_type, discount_value,
                                    max_discount, min_order_value, usage_limit, per_user_limit,
                                    valid_from, valid_till, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """, [
                coupon_id, code, description, discount_type, discount_value,
                max_discount, min_order_value, usage_limit, per_user_limit,
                valid_from, valid_till,
            ])
    except IntegrityError:
        return JsonResponse({'error': 'Coupon code already exists'}, status=409)

    invalidate_coupons()

    return JsonResponse({
        'id': coupon_id,
        'code': code,
        'message': 'Coupon created successfully',
    }, status=201)


# ============================================================================
# GET /admin/coupons - List all coupons
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def list_coupons(request):
    """List all coupons with filters."""
    is_active = request.GET.get('is_active')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit

    where_clauses = []
    params = []

    if is_active is not None:
        where_clauses.append('is_active = %s')
        params.append(is_active.lower() == 'true')

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM coupons {where_sql}", params)
        total = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT id, code, description, discount_type, discount_value,
                   max_discount, min_order_value, usage_limit, per_user_limit,
                   valid_from, valid_till, is_active, created_at
            FROM coupons
            {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])

        coupons = []
        for row in cursor.fetchall():
            cursor2 = connection.cursor()
            cursor2.execute("SELECT COUNT(*) FROM coupon_usage WHERE coupon_id = %s", [row[0]])
            used_count = cursor2.fetchone()[0]
            cursor2.close()

            coupons.append({
                'id': row[0],
                'code': row[1],
                'description': row[2],
                'discount_type': row[3],
                'discount_value': float(row[4]),
                'max_discount': float(row[5]) if row[5] else None,
                'min_order_value': float(row[6]),
                'usage_limit': row[7],
                'per_user_limit': row[8],
                'valid_from': row[9].isoformat() if row[9] else None,
                'valid_till': row[10].isoformat() if row[10] else None,
                'is_active': bool(row[11]),
                'created_at': row[12].isoformat() if row[12] else None,
                'used_count': used_count,
            })

    return JsonResponse({
        'total': total,
        'page': page,
        'limit': limit,
        'coupons': coupons,
    })


# ============================================================================
# PATCH /admin/coupons/<id> - Update a coupon
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_admin
def update_coupon(request, coupon_id):
    """Update a coupon's fields."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    allowed_fields = {
        'description', 'discount_value', 'max_discount', 'min_order_value',
        'usage_limit', 'per_user_limit', 'valid_from', 'valid_till', 'is_active'
    }

    updates = []
    params = []

    for field in allowed_fields:
        if field in data:
            updates.append(f'{field} = %s')
            params.append(data[field])

    if not updates:
        return JsonResponse({'error': 'No valid fields to update'}, status=400)

    params.append(coupon_id)

    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE coupons SET {', '.join(updates)} WHERE id = %s", params)
        if cursor.rowcount == 0:
            return JsonResponse({'error': 'Coupon not found'}, status=404)

    invalidate_coupons()

    return JsonResponse({'message': 'Coupon updated successfully'})


# ============================================================================
# PATCH /admin/coupons/<id>/toggle - Activate/deactivate a coupon
# ============================================================================
@csrf_exempt
@require_http_methods(['PATCH'])
@require_admin
def toggle_coupon(request, coupon_id):
    """Toggle coupon active status."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT is_active FROM coupons WHERE id = %s", [coupon_id])
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'error': 'Coupon not found'}, status=404)

        new_status = not bool(row[0])
        cursor.execute("UPDATE coupons SET is_active = %s WHERE id = %s", [new_status, coupon_id])

    invalidate_coupons()

    return JsonResponse({'coupon_id': coupon_id, 'is_active': new_status})


# ============================================================================
# DELETE /admin/coupons/<id> - Delete a coupon
# ============================================================================
@csrf_exempt
@require_http_methods(['DELETE'])
@require_admin
def delete_coupon(request, coupon_id):
    """Permanently delete a coupon."""
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM coupons WHERE id = %s", [coupon_id])
        if cursor.rowcount == 0:
            return JsonResponse({'error': 'Coupon not found'}, status=404)

    invalidate_coupons()

    return JsonResponse({'message': 'Coupon deleted successfully'})


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('admin/coupons', list_coupons, name='admin-coupons-list'),
    path('admin/coupons/create', create_coupon, name='admin-coupon-create'),
    path('admin/coupons/<str:coupon_id>', update_coupon, name='admin-coupon-update'),
    path('admin/coupons/<str:coupon_id>/toggle', toggle_coupon, name='admin-coupon-toggle'),
    path('admin/coupons/<str:coupon_id>/delete', delete_coupon, name='admin-coupon-delete'),
]