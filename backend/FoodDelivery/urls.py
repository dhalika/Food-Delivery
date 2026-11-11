"""
Main URL configuration for FoodDelivery project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('', include('auth.Unified_auth')),

    # Admin
    path('', include('core.Admin.dashboard')),
    path('', include('core.Admin.manage_users')),
    path('', include('core.Admin.manage_restaurants')),
    path('', include('core.Admin.manage_orders')),
    path('', include('core.Admin.manage_coupons')),

    # Restaurant Owner
    path('', include('core.Restaurant.restaurant_profile')),
    path('', include('core.Restaurant.restaurant_timings')),
    path('', include('core.Restaurant.menu_management')),
    path('', include('core.Restaurant.incoming_orders')),
    path('', include('core.Restaurant.sales_dashboard')),
    path('', include('core.Restaurant.restaurant_reviews')),
    path('', include('core.Restaurant.restaurant_notifications')),

    # Customer
    path('', include('core.Customer.browse_restaurants')),
    path('', include('core.Customer.restaurant_menu')),
    path('', include('core.Customer.cart')),
    path('', include('core.Customer.apply_coupon')),
    path('', include('core.Customer.place_order')),
    path('', include('core.Customer.order_history')),
    path('', include('core.Customer.track_order')),
    path('', include('core.Customer.review')),
    path('', include('core.Customer.address')),
    path('', include('core.Customer.customer_notifications')),
    path('', include('core.Customer.group_order')),
    path('', include('core.Customer.ai_recommendations')),

    # Payment
    path('', include('core.Payment.razorpay')),
    path('', include('core.Payment.webhook_handler')),

    # Delivery Partner
    path('', include('core.Delivery.availability')),
    path('', include('core.Delivery.assigned_orders')),
    path('', include('core.Delivery.order_actions')),
    path('', include('core.Delivery.update_location')),
    path('', include('core.Delivery.auto_assignment')),
    path('', include('core.Delivery.delivery_notifications')),

    # Notifications (unified)
    path('', include('core.Notification.notification_service')),

    # Admin Cache
    path('', include('core.Cache.admin_cache')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)