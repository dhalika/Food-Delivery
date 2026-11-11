"""
Cache invalidation - helpers to invalidate cache when data changes.
Called from mutation endpoints (POST/PUT/PATCH/DELETE).
"""
from core.Cache.cache_service import cache_delete, cache_delete_pattern
from core.Cache.cache_keys import (
    RESTAURANT_LIST, RESTAURANT_DETAIL, RESTAURANT_MENU,
    RESTAURANT_CATEGORIES, RESTAURANT_TIMINGS,
    USER_PROFILE, USER_ADDRESSES, COUPONS_ACTIVE, ADMIN_STATS,
    make_key,
)


def invalidate_restaurant(restaurant_id):
    """Invalidate all caches related to a restaurant."""
    cache_delete(make_key(RESTAURANT_DETAIL, restaurant_id=restaurant_id))
    cache_delete(make_key(RESTAURANT_MENU, restaurant_id=restaurant_id))
    cache_delete(make_key(RESTAURANT_CATEGORIES, restaurant_id=restaurant_id))
    cache_delete(make_key(RESTAURANT_TIMINGS, restaurant_id=restaurant_id))
    cache_delete(RESTAURANT_LIST)
    # Invalidate nearby cache (pattern-based)
    cache_delete_pattern('restaurants:nearby')


def invalidate_menu(restaurant_id):
    """Invalidate menu cache for a restaurant."""
    cache_delete(make_key(RESTAURANT_MENU, restaurant_id=restaurant_id))
    cache_delete(make_key(RESTAURANT_CATEGORIES, restaurant_id=restaurant_id))


def invalidate_user_profile(user_id):
    """Invalidate user profile cache."""
    cache_delete(make_key(USER_PROFILE, user_id=user_id))


def invalidate_user_addresses(user_id):
    """Invalidate user addresses cache."""
    cache_delete(make_key(USER_ADDRESSES, user_id=user_id))


def invalidate_coupons():
    """Invalidate coupons list cache."""
    cache_delete(COUPONS_ACTIVE)


def invalidate_admin_stats():
    """Invalidate admin stats cache."""
    cache_delete(ADMIN_STATS)