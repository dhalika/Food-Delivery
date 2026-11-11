"""
Seed script — Populates database with sample data.
Run: python manage.py shell < scripts/seed_data.py
OR: python scripts/seed_data.py
"""
import os
import django
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FoodDelivery.settings')
django.setup()

from django.db import connection
from auth.password_utils import hash_password

print("🥡 HongKong Seed Data Script Starting...")
print("=" * 50)


# =============================================================================
# 1. CLEAR EXISTING DATA (optional - uncomment if needed)
# =============================================================================
# with connection.cursor() as cursor:
#     cursor.execute("DELETE FROM menu_items")
#     cursor.execute("DELETE FROM categories")
#     cursor.execute("DELETE FROM restaurants")
#     cursor.execute("DELETE FROM users WHERE role='restaurant_owner'")

# =============================================================================
# 2. CREATE RESTAURANT OWNERS
# =============================================================================
print("\n👤 Creating restaurant owners...")
owners_data = [
    ("Rajesh Kumar", "rajesh@hongkong.com", "9000000001"),
    ("Priya Sharma", "priya@hongkong.com", "9000000002"),
    ("Amit Singh", "amit@hongkong.com", "9000000003"),
    ("Sneha Reddy", "sneha@hongkong.com", "9000000004"),
    ("Vikram Patel", "vikram@hongkong.com", "9000000005"),
]
password_hash = hash_password("owner123")
owner_ids = []

with connection.cursor() as cursor:
    for name, email, phone in owners_data:
        owner_id = str(uuid.uuid4())
        try:
            cursor.execute("""
                INSERT INTO users (id, name, email, password_hash, phone, role, is_active, is_available)
                VALUES (%s, %s, %s, %s, %s, 'restaurant_owner', TRUE, FALSE)
            """, [owner_id, name, email, password_hash, phone])
            owner_ids.append(owner_id)
            print(f"  ✓ {name}")
        except Exception as e:
            # Owner already exists, fetch existing
            cursor.execute("SELECT id FROM users WHERE email = %s", [email])
            row = cursor.fetchone()
            if row:
                owner_ids.append(row[0])
                print(f"  ⊙ {name} (already exists)")


# =============================================================================
# 3. CREATE RESTAURANTS
# =============================================================================
print("\n🏪 Creating restaurants...")
restaurants_data = [
    # (name, cuisine_type, city, phone, lat, lng, avg_rating, delivery_time, min_order, banner_url)
    ("Pizza Palace", "Pizza, Italian", "Hyderabad", "9888800001", 17.4065, 78.4772, 4.5, 30, 199,
     "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600"),

    ("Biryani House", "Biryani, Indian", "Hyderabad", "9888800002", 17.4239, 78.4738, 4.3, 25, 249,
     "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600"),

    ("Dragon Wok", "Chinese, Asian", "Hyderabad", "9888800003", 17.4474, 78.3762, 4.2, 35, 199,
     "https://images.unsplash.com/photo-1526318896980-cf78c088247c?w=600"),

    ("Burger King Kitchen", "Burger, Fast Food", "Hyderabad", "9888800004", 17.4126, 78.4071, 4.4, 20, 149,
     "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600"),

    ("South Spice", "South Indian", "Hyderabad", "9888800005", 17.4399, 78.4983, 4.6, 25, 99,
     "https://images.unsplash.com/photo-1630383249896-424e482df921?w=600"),

    ("Punjabi Dhaba", "North Indian, Punjabi", "Hyderabad", "9888800006", 17.3850, 78.4867, 4.1, 40, 199,
     "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600"),

    ("Sweet Treats", "Desserts, Beverages", "Hyderabad", "9888800007", 17.4280, 78.4484, 4.7, 20, 99,
     "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=600"),

    ("Pasta & Co", "Pizza, Italian, Pasta", "Hyderabad", "9888800008", 17.4499, 78.3908, 4.3, 30, 249,
     "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=600"),

    ("Hyderabadi Biryani Center", "Biryani, Mughlai", "Hyderabad", "9888800009", 17.3616, 78.4747, 4.5, 30, 299,
     "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600"),

    ("Cafe Mocha", "Beverages, Snacks", "Hyderabad", "9888800010", 17.4432, 78.3772, 4.4, 15, 149,
     "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=600"),
]

restaurant_ids = []
with connection.cursor() as cursor:
    for i, data in enumerate(restaurants_data):
        name, cuisine, city, phone, lat, lng, rating, delivery_time, min_order, banner = data
        owner_id = owner_ids[i % len(owner_ids)]
        restaurant_id = str(uuid.uuid4())
        try:
            cursor.execute("""
                INSERT INTO restaurants (
                    id, owner_id, name, description, cuisine_type, phone, email,
                    banner_url, address, city, pincode, lat, lng,
                    avg_rating, total_reviews, avg_delivery_time, min_order_value,
                    is_active, is_verified
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, TRUE)
            """, [
                restaurant_id, owner_id, name, f"Delicious {cuisine.split(',')[0]} delivered fresh!",
                cuisine, phone, f"contact@{name.lower().replace(' ', '')}.com",
                banner, f"{i+1} Main Street, {city}", city, "500001",
                lat, lng, rating, 50 + i*10, delivery_time, min_order
            ])
            restaurant_ids.append((restaurant_id, cuisine))
            print(f"  ✓ {name} ({cuisine})")
        except Exception as e:
            print(f"  ✗ {name}: {e}")


# =============================================================================
# 4. CREATE CATEGORIES + MENU ITEMS
# =============================================================================
print("\n🍽️ Creating menu items...")

MENU_TEMPLATES = {
    "Pizza": [
        ("Starters", [
            ("Garlic Bread", 149, True, "Toasted bread with garlic butter"),
            ("Cheesy Nachos", 199, True, "Loaded with cheese and jalapeños"),
        ]),
        ("Pizzas", [
            ("Margherita Pizza", 299, True, "Classic cheese & tomato"),
            ("Pepperoni Pizza", 399, False, "Loaded pepperoni & mozzarella"),
            ("Veggie Supreme", 349, True, "Bell peppers, olives, onions, corn"),
            ("BBQ Chicken Pizza", 449, False, "Grilled chicken with BBQ sauce"),
        ]),
        ("Beverages", [
            ("Coca Cola", 60, True, "500ml"),
            ("Fresh Lime Soda", 80, True, ""),
        ]),
    ],
    "Biryani": [
        ("Biryani", [
            ("Chicken Biryani", 299, False, "Hyderabadi style dum biryani"),
            ("Mutton Biryani", 449, False, "Tender mutton with aromatic rice"),
            ("Veg Biryani", 199, True, "Mixed vegetables biryani"),
            ("Paneer Biryani", 249, True, "Paneer cubes in spiced rice"),
        ]),
        ("Starters", [
            ("Chicken 65", 249, False, "Spicy fried chicken"),
            ("Paneer Tikka", 229, True, "Grilled paneer with spices"),
        ]),
        ("Desserts", [
            ("Double Ka Meetha", 99, True, "Hyderabadi bread pudding"),
            ("Qubani Ka Meetha", 129, True, "Apricot dessert"),
        ]),
    ],
    "Chinese": [
        ("Soups", [
            ("Hot & Sour Soup (Veg)", 129, True, ""),
            ("Manchow Soup", 149, True, "With crispy noodles"),
        ]),
        ("Main Course", [
            ("Chicken Fried Rice", 249, False, ""),
            ("Veg Hakka Noodles", 199, True, ""),
            ("Schezwan Chicken", 299, False, "Spicy Schezwan sauce"),
            ("Paneer Manchurian", 229, True, "Dry style"),
        ]),
    ],
    "Burger": [
        ("Burgers", [
            ("Classic Chicken Burger", 149, False, "Grilled chicken patty"),
            ("Veg Delight Burger", 99, True, "Crispy veg patty"),
            ("Double Cheese Burger", 199, False, "Loaded cheese"),
            ("Mexican Spicy Burger", 179, True, "Spicy bean patty"),
        ]),
        ("Sides", [
            ("French Fries", 99, True, ""),
            ("Peri Peri Fries", 129, True, ""),
        ]),
    ],
    "South Indian": [
        ("Breakfast", [
            ("Masala Dosa", 99, True, "Crispy dosa with potato filling"),
            ("Idli Sambar (4)", 79, True, "Soft idlis with sambar"),
            ("Vada Sambar (2)", 69, True, "Crispy medu vada"),
            ("Upma", 89, True, "Semolina breakfast"),
        ]),
        ("Rice", [
            ("Curd Rice", 129, True, "With pickle"),
            ("Lemon Rice", 119, True, ""),
        ]),
    ],
    "North Indian": [
        ("Breads", [
            ("Butter Naan", 49, True, ""),
            ("Garlic Naan", 69, True, ""),
            ("Tandoori Roti", 29, True, ""),
        ]),
        ("Main Course", [
            ("Butter Chicken", 349, False, "Rich creamy gravy"),
            ("Dal Makhani", 199, True, "Slow-cooked lentils"),
            ("Paneer Butter Masala", 249, True, ""),
            ("Chicken Tikka Masala", 329, False, ""),
        ]),
    ],
    "Desserts": [
        ("Desserts", [
            ("Chocolate Cake", 149, True, "Rich dark chocolate"),
            ("Red Velvet Pastry", 99, True, ""),
            ("Ice Cream Sundae", 199, True, "3 scoops with toppings"),
            ("Gulab Jamun (4)", 79, True, ""),
        ]),
        ("Beverages", [
            ("Cold Coffee", 149, True, ""),
            ("Mango Shake", 129, True, ""),
        ]),
    ],
    "Beverages": [
        ("Hot Beverages", [
            ("Cappuccino", 129, True, ""),
            ("Latte", 139, True, ""),
            ("Masala Chai", 49, True, ""),
        ]),
        ("Cold Beverages", [
            ("Iced Latte", 159, True, ""),
            ("Cold Coffee", 149, True, ""),
            ("Fresh Juice", 99, True, ""),
        ]),
        ("Snacks", [
            ("Sandwich", 149, True, "Grilled veg sandwich"),
            ("Pasta", 199, True, "White sauce pasta"),
        ]),
    ],
}

total_items = 0
with connection.cursor() as cursor:
    for restaurant_id, cuisine in restaurant_ids:
        # Pick menu template based on cuisine
        primary_cuisine = cuisine.split(',')[0].strip()

        # Match to template
        template = None
        for key in MENU_TEMPLATES:
            if key.lower() in primary_cuisine.lower() or primary_cuisine.lower() in key.lower():
                template = MENU_TEMPLATES[key]
                break

        if not template:
            template = MENU_TEMPLATES.get(primary_cuisine, MENU_TEMPLATES["Pizza"])

        sort = 0
        for category_name, items in template:
            cat_id = str(uuid.uuid4())
            try:
                cursor.execute("""
                    INSERT INTO categories (id, restaurant_id, name, sort_order, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                """, [cat_id, restaurant_id, category_name, sort])
                sort += 1

                for item_name, price, is_veg, desc in items:
                    item_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO menu_items (
                            id, restaurant_id, category_id, name, description, price,
                            is_veg, is_available, preparation_time
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                    """, [item_id, restaurant_id, cat_id, item_name, desc, price, is_veg, 20])
                    total_items += 1
            except Exception as e:
                pass

print(f"  ✓ {total_items} menu items created")


# =============================================================================
# 5. CREATE COUPONS
# =============================================================================
print("\n🎟️ Creating coupons...")
now = datetime.now()
future = now + timedelta(days=90)

coupons = [
    ("WELCOME50", "percentage", 50, 100, 0, "50% off up to ₹100 on first order"),
    ("FLAT100", "flat", 100, None, 299, "₹100 off on orders above ₹299"),
    ("SAVE20", "percentage", 20, 50, 199, "20% off up to ₹50"),
    ("MEGADEAL", "flat", 200, None, 599, "₹200 off on orders above ₹599"),
    ("HONGKONG10", "percentage", 10, 150, 0, "10% off up to ₹150"),
]

with connection.cursor() as cursor:
    for code, dtype, value, max_disc, min_order, desc in coupons:
        try:
            cursor.execute("""
                INSERT INTO coupons (
                    id, code, description, discount_type, discount_value,
                    max_discount, min_order_value, per_user_limit,
                    valid_from, valid_till, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 3, %s, %s, TRUE)
            """, [str(uuid.uuid4()), code, desc, dtype, value, max_disc, min_order, now, future])
            print(f"  ✓ {code} — {desc}")
        except Exception as e:
            print(f"  ⊙ {code} already exists")


# =============================================================================
# DONE
# =============================================================================
print("\n" + "=" * 50)
print("🎉 SEED DATA COMPLETE!")
print(f"✓ {len(owner_ids)} restaurant owners")
print(f"✓ {len(restaurant_ids)} restaurants")
print(f"✓ {total_items} menu items")
print(f"✓ {len(coupons)} coupons")
print("\n🔑 Owner login: email + 'owner123'")
print("🎟️ Try coupons: WELCOME50, FLAT100, SAVE20, MEGADEAL, HONGKONG10")