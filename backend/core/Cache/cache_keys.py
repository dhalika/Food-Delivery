"""
Central registry of all cache keys and their TTLs.
Keep keys consistent across modules.
"""

# ============================================================================
# CACHE KEY PATTERNS
# ============================================================================
RESTAURANT_LIST = 'restaurants:list:v1'                    # All active restaurants
RESTAURANT_DETAIL = 'restaurant:detail:{restaurant_id}'    # Single restaurant
RESTAURANT_NEARBY = 'restaurants:nearby:{lat}:{lng}:{radius}'  # Nearby search

RESTAURANT_MENU = 'restaurant:menu:{restaurant_id}'        # Full menu
RESTAURANT_CATEGORIES = 'restaurant:categories:{restaurant_id}'
RESTAURANT_TIMINGS = 'restaurant:timings:{restaurant_id}'

USER_PROFILE = 'user:profile:{user_id}'                    # User profile
USER_ADDRESSES = 'user:addresses:{user_id}'                # User addresses

COUPONS_ACTIVE = 'coupons:active:v1'                       # Active coupons list

ADMIN_STATS = 'admin:stats:v1'                             # Admin dashboard stats

# ============================================================================
# TTL (Time-To-Live) in seconds
# ============================================================================
TTL_RESTAURANT_LIST = 300           # 5 minutes
TTL_RESTAURANT_DETAIL = 600         # 10 minutes
TTL_NEARBY = 180                    # 3 minutes
TTL_MENU = 600                      # 10 minutes
TTL_CATEGORIES = 1800               # 30 minutes
TTL_TIMINGS = 3600                  # 1 hour
TTL_USER_PROFILE = 1800             # 30 minutes
TTL_USER_ADDRESSES = 1800           # 30 minutes
TTL_COUPONS = 300                   # 5 minutes
TTL_ADMIN_STATS = 120               # 2 minutes


def make_key(pattern, **kwargs):
    """Format a cache key with parameters."""
    return pattern.format(**kwargs)