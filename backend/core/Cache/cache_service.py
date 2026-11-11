"""
Cache service - wraps Django's cache with JSON serialization and logging.
"""
import json
import logging
from django.core.cache import cache

logger = logging.getLogger('core')


def cache_get(key):
    """Get value from cache. Returns None if miss or error."""
    try:
        value = cache.get(key)
        if value is not None:
            logger.debug(f'CACHE HIT: {key}')
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
        logger.debug(f'CACHE MISS: {key}')
        return None
    except Exception as e:
        logger.error(f'cache_get error for {key}: {e}')
        return None


def cache_set(key, value, ttl=300):
    """Set value in cache with TTL (seconds). Returns True on success."""
    try:
        serialized = json.dumps(value, default=str)
        cache.set(key, serialized, timeout=ttl)
        logger.debug(f'CACHE SET: {key} (ttl={ttl}s)')
        return True
    except Exception as e:
        logger.error(f'cache_set error for {key}: {e}')
        return False


def cache_delete(key):
    """Delete a key from cache."""
    try:
        cache.delete(key)
        logger.debug(f'CACHE DEL: {key}')
        return True
    except Exception as e:
        logger.error(f'cache_delete error for {key}: {e}')
        return False


def cache_delete_pattern(pattern):
    """
    Delete all keys matching a pattern (uses Redis SCAN).
    Example: cache_delete_pattern('restaurant:menu:*')
    """
    try:
        from django_redis import get_redis_connection
        conn = get_redis_connection('default')
        count = 0
        for key in conn.scan_iter(f'*{pattern}*'):
            conn.delete(key)
            count += 1
        logger.debug(f'CACHE PATTERN DEL: {pattern} ({count} keys)')
        return count
    except Exception as e:
        logger.error(f'cache_delete_pattern error for {pattern}: {e}')
        return 0


def cache_clear_all():
    """Clear entire cache. Use only for admin/debug."""
    try:
        cache.clear()
        logger.warning('CACHE CLEAR ALL')
        return True
    except Exception as e:
        logger.error(f'cache_clear_all error: {e}')
        return False