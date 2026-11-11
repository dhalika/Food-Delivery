from django.contrib import admin
from core.models import (
    User, Address, Restaurant, RestaurantTiming, Category, MenuItem,
    Cart, CartItem, Coupon, CouponUsage, Order, OrderItem,
    OrderStatusHistory, Payment, Review, DeliveryLocation, Notification
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'role', 'phone', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'email', 'phone']


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'cuisine_type', 'avg_rating', 'is_active', 'is_verified']
    list_filter = ['is_active', 'is_verified', 'city']
    search_fields = ['name', 'city']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'price', 'is_veg', 'is_available']
    list_filter = ['is_veg', 'is_available']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'restaurant', 'status', 'final_amount', 'placed_at']
    list_filter = ['status', 'payment_method']


admin.site.register(Address)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Coupon)
admin.site.register(CouponUsage)
admin.site.register(OrderItem)
admin.site.register(OrderStatusHistory)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(DeliveryLocation)
admin.site.register(Notification)
admin.site.register(RestaurantTiming)