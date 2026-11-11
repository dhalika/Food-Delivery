"""
Core models - matches the 17-table MySQL schema.
Using managed=False since we created tables manually via SQL script.
"""
from django.db import models
import uuid


# ==============================================================================
# 1. USERS
# ==============================================================================
class User(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('restaurant_owner', 'Restaurant Owner'),
        ('delivery_partner', 'Delivery Partner'),
        ('admin', 'Admin'),
    )

    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    avatar_url = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        managed = False

    def __str__(self):
        return f"{self.name} ({self.role})"


# ==============================================================================
# 2. ADDRESSES
# ==============================================================================
class Address(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    label = models.CharField(max_length=50)
    full_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'addresses'
        managed = False


# ==============================================================================
# 3. RESTAURANTS
# ==============================================================================
class Restaurant(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, db_column='owner_id')
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    cuisine_type = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    logo_url = models.CharField(max_length=500, null=True, blank=True)
    banner_url = models.CharField(max_length=500, null=True, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lng = models.DecimalField(max_digits=10, decimal_places=7)
    avg_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    total_reviews = models.IntegerField(default=0)
    avg_delivery_time = models.IntegerField(null=True, blank=True)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurants'
        managed = False


# ==============================================================================
# 4. RESTAURANT_TIMINGS
# ==============================================================================
class RestaurantTiming(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    day_of_week = models.SmallIntegerField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        db_table = 'restaurant_timings'
        managed = False


# ==============================================================================
# 5. CATEGORIES
# ==============================================================================
class Category(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    name = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        managed = False


# ==============================================================================
# 6. MENU_ITEMS
# ==============================================================================
class MenuItem(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, db_column='category_id')
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.CharField(max_length=500, null=True, blank=True)
    is_veg = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    preparation_time = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'menu_items'
        managed = False


# ==============================================================================
# 7. CARTS
# ==============================================================================
class Cart(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    customer = models.OneToOneField(User, on_delete=models.CASCADE, db_column='customer_id')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, db_column='restaurant_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'
        managed = False


# ==============================================================================
# 8. CART_ITEMS
# ==============================================================================
class CartItem(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, db_column='cart_id')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, db_column='menu_item_id')
    item_name = models.CharField(max_length=200)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_items'
        managed = False


# ==============================================================================
# 9. COUPONS
# ==============================================================================
class Coupon(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    discount_type = models.CharField(max_length=10)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    usage_limit = models.IntegerField(null=True, blank=True)
    per_user_limit = models.IntegerField(default=1)
    valid_from = models.DateTimeField()
    valid_till = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupons'
        managed = False


# ==============================================================================
# 10. COUPON_USAGE
# ==============================================================================
class CouponUsage(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, db_column='coupon_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    order_id = models.CharField(max_length=36, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_usage'
        managed = False


# ==============================================================================
# 11. ORDERS
# ==============================================================================
class Order(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, db_column='customer_id', related_name='customer_orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    delivery_partner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column='delivery_partner_id', related_name='delivery_orders')
    delivery_address = models.ForeignKey(Address, on_delete=models.CASCADE, db_column='delivery_address_id')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, db_column='coupon_id')
    status = models.CharField(max_length=20, default='placed')
    item_total = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10)
    special_instructions = models.TextField(null=True, blank=True)
    cancel_reason = models.TextField(null=True, blank=True)
    cancelled_by = models.CharField(max_length=10, null=True, blank=True)
    estimated_delivery_time = models.IntegerField(null=True, blank=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        managed = False


# ==============================================================================
# 12. ORDER_ITEMS
# ==============================================================================
class OrderItem(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, db_column='menu_item_id')
    item_name = models.CharField(max_length=200)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'
        managed = False


# ==============================================================================
# 13. ORDER_STATUS_HISTORY
# ==============================================================================
class OrderStatusHistory(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column='changed_by')
    note = models.CharField(max_length=255, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_status_history'
        managed = False


# ==============================================================================
# 14. PAYMENTS
# ==============================================================================
class Payment(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, db_column='order_id')
    method = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        managed = False


# ==============================================================================
# 15. REVIEWS
# ==============================================================================
class Review(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, db_column='order_id')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, db_column='customer_id')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, db_column='restaurant_id')
    rating = models.SmallIntegerField()
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        managed = False


# ==============================================================================
# 16. DELIVERY_LOCATIONS
# ==============================================================================
class DeliveryLocation(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    delivery_partner = models.ForeignKey(User, on_delete=models.CASCADE, db_column='delivery_partner_id')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_column='order_id')
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lng = models.DecimalField(max_digits=10, decimal_places=7)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delivery_locations'
        managed = False


# ==============================================================================
# 17. NOTIFICATIONS
# ==============================================================================
class Notification(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=15)
    reference_id = models.CharField(max_length=36, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        managed = False