"""
Admin endpoints for cache management - view stats, clear cache.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import path

from auth.guards import require_admin
from core.Cache.cache_service import cache_clear_all, cache_delete_pattern


# ============================================================================
# POST /admin/cache/clear-all - Clear entire cache
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_admin
def clear_all_cache(request):
    """Admin: Clear entire Redis cache."""
    success = cache_clear_all()
    return JsonResponse({
        'success': success,
        'message': 'All cache cleared' if success else 'Failed to clear cache',
    })


# ============================================================================
# POST /admin/cache/clear-pattern - Clear cache by pattern
# ============================================================================
@csrf_exempt
@require_http_methods(['POST'])
@require_admin
def clear_cache_pattern(request):
    """Admin: Clear cache keys matching a pattern (e.g. 'restaurant:menu')."""
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    pattern = data.get('pattern', '').strip()
    if not pattern:
        return JsonResponse({'error': 'pattern required'}, status=400)

    count = cache_delete_pattern(pattern)
    return JsonResponse({
        'pattern': pattern,
        'keys_deleted': count,
    })


# ============================================================================
# GET /admin/cache/stats - Redis cache stats
# ============================================================================
@csrf_exempt
@require_http_methods(['GET'])
@require_admin
def cache_stats(request):
    """Get Redis cache stats."""
    try:
        from django_redis import get_redis_connection
        conn = get_redis_connection('default')
        info = conn.info()

        return JsonResponse({
            'used_memory_human': info.get('used_memory_human'),
            'connected_clients': info.get('connected_clients'),
            'total_keys': conn.dbsize(),
            'uptime_seconds': info.get('uptime_in_seconds'),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'hit_rate': round(
                info.get('keyspace_hits', 0) /
                max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 2
            ),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    path('admin/cache/stats', cache_stats, name='admin-cache-stats'),
    path('admin/cache/clear-all', clear_all_cache, name='admin-cache-clear'),
    path('admin/cache/clear-pattern', clear_cache_pattern, name='admin-cache-clear-pattern'),
]