"""
Seed script - populates database with realistic restaurant data.
Run with: python seed_data.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_system.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from restaurant.models import Category, MenuItem, Table, Reservation, Order, OrderItem, InventoryItem

print("Seeding Restaurant Management System...")

# Admin
admin, _ = User.objects.get_or_create(username='admin', defaults={
    'email': 'admin@bistro.com', 'is_staff': True, 'is_superuser': True,
    'first_name': 'Admin', 'last_name': 'Manager'
})
admin.set_password('admin123')
admin.save()

# Staff
staff_data = [
    ('waiter1', 'waiter1@bistro.com', 'Ali', 'Hasanov'),
    ('waiter2', 'waiter2@bistro.com', 'Leyla', 'Mammadova'),
    ('manager1', 'manager@bistro.com', 'Fuad', 'Aliyev'),
]
staff_users = []
for username, email, first, last in staff_data:
    u, _ = User.objects.get_or_create(username=username, defaults={
        'email': email, 'first_name': first, 'last_name': last, 'is_staff': True
    })
    u.set_password('password123')
    u.save()
    staff_users.append(u)

# Categories
cats = {}
for name, desc in [
    ('Starters', 'Appetizers and small plates to begin your meal'),
    ('Soups & Salads', 'Fresh soups and crisp salads'),
    ('Main Course', 'Hearty mains from grill and oven'),
    ('Pasta & Risotto', 'Italian classics made fresh daily'),
    ('Grills', 'Premium cuts and kebabs from our charcoal grill'),
    ('Desserts', 'Sweet endings to your meal'),
    ('Beverages', 'Hot, cold, and alcoholic drinks'),
]:
    c, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
    cats[name] = c

# Menu items
menu_items = [
    # Starters
    ('Hummus & Pita', 'Creamy chickpea hummus with warm pita bread and olive oil drizzle', 6.50, 'Starters', True, True, True, 10, 280),
    ('Bruschetta al Pomodoro', 'Toasted sourdough with diced tomatoes, fresh basil and garlic', 7.00, 'Starters', True, True, False, 10, 220),
    ('Chicken Wings (6 pcs)', 'Crispy wings with BBQ or buffalo sauce, celery and blue cheese dip', 9.50, 'Starters', False, False, True, 15, 480),
    ('Calamari Fritti', 'Lightly battered squid rings with lemon aioli', 10.00, 'Starters', False, False, False, 12, 350),

    # Soups & Salads
    ('Tom Yum Soup', 'Spicy Thai soup with shrimp, mushrooms, lemongrass and coconut milk', 8.00, 'Soups & Salads', False, False, True, 15, 190),
    ('Caesar Salad', 'Romaine lettuce, parmesan, croutons, Caesar dressing', 9.00, 'Soups & Salads', False, False, False, 8, 320),
    ('Greek Salad', 'Tomatoes, cucumber, olives, feta cheese, oregano, olive oil', 8.50, 'Soups & Salads', True, False, True, 7, 240),

    # Main Course
    ('Grilled Sea Bass', 'Whole sea bass with lemon butter, capers and seasonal vegetables', 22.00, 'Main Course', False, False, True, 25, 420),
    ('Chicken Schnitzel', 'Breaded chicken breast with french fries and coleslaw', 15.50, 'Main Course', False, False, False, 20, 650),
    ('Vegetable Stir-Fry', 'Seasonal vegetables wok-tossed in soy-ginger sauce with jasmine rice', 12.00, 'Main Course', True, True, False, 15, 380),

    # Pasta
    ('Spaghetti Carbonara', 'Spaghetti, pancetta, eggs, pecorino, black pepper', 14.00, 'Pasta & Risotto', False, False, False, 18, 620),
    ('Penne Arrabbiata', 'Penne with spicy tomato sauce, garlic and fresh chilli', 12.50, 'Pasta & Risotto', True, True, False, 15, 480),
    ('Mushroom Risotto', 'Arborio rice with porcini mushrooms, parmesan and truffle oil', 15.00, 'Pasta & Risotto', True, False, True, 22, 540),

    # Grills
    ('Ribeye Steak 300g', '300g prime ribeye, choice of sauce, fries or mashed potato', 32.00, 'Grills', False, False, True, 25, 850),
    ('Lamb Chops (3 pcs)', 'Marinated lamb chops with mint sauce and grilled vegetables', 28.00, 'Grills', False, False, True, 25, 720),
    ('Mixed Kebab Platter', 'Chicken, lamb and beef kebab with rice, salad and flatbread', 24.00, 'Grills', False, False, True, 25, 780),

    # Desserts
    ('Tiramisu', 'Classic Italian dessert with mascarpone, espresso and cocoa', 7.50, 'Desserts', True, False, False, 5, 380),
    ('Chocolate Lava Cake', 'Warm chocolate cake with molten centre, vanilla ice cream', 8.00, 'Desserts', True, False, False, 12, 450),
    ('Baklava (3 pcs)', 'Flaky pastry with walnuts, honey and rosewater syrup', 6.00, 'Desserts', True, True, False, 3, 310),

    # Beverages
    ('Fresh Orange Juice', 'Freshly squeezed orange juice, 300ml', 4.00, 'Beverages', True, True, True, 3, 140),
    ('Espresso', 'Double shot espresso', 2.50, 'Beverages', True, True, True, 3, 10),
    ('Lemonade', 'House-made lemonade with mint', 4.50, 'Beverages', True, True, True, 3, 90),
    ('House Red Wine (glass)', 'Shiraz, full-bodied with dark fruit notes', 7.00, 'Beverages', True, True, True, 1, 125),
]

menu_objects = {}
for name, desc, price, cat_name, is_veg, is_vegan, is_gf, prep_time, cal in menu_items:
    item, _ = MenuItem.objects.get_or_create(name=name, defaults={
        'description': desc, 'price': price, 'category': cats[cat_name],
        'is_vegetarian': is_veg, 'is_vegan': is_vegan, 'is_gluten_free': is_gf,
        'preparation_time': prep_time, 'calories': cal, 'is_available': True
    })
    menu_objects[name] = item

# Tables
table_data = [
    (1, 2, 'Window'), (2, 2, 'Window'), (3, 4, 'Main Hall'), (4, 4, 'Main Hall'),
    (5, 4, 'Main Hall'), (6, 6, 'Main Hall'), (7, 6, 'Terrace'),
    (8, 8, 'Terrace'), (9, 10, 'Private Room'), (10, 12, 'Private Room'),
]
tables = {}
for num, cap, loc in table_data:
    t, _ = Table.objects.get_or_create(number=num, defaults={'capacity': cap, 'location': loc, 'status': 'available'})
    tables[num] = t

# Set some tables as occupied
tables[3].status = 'occupied'; tables[3].save()
tables[7].status = 'reserved'; tables[7].save()

# Reservations
now = timezone.now()
reservations_data = [
    ('Rashad Huseynov', '+994501234567', 'rashad@mail.com', 7, 4, now + timedelta(hours=2), 'confirmed', 'Window table preferred'),
    ('Elena Petrova', '+994552345678', 'elena@mail.com', 9, 3, now + timedelta(hours=4), 'confirmed', 'Birthday celebration - please prepare cake'),
    ('David Chen', '+994703456789', '', 10, 2, now + timedelta(days=1, hours=1), 'pending', ''),
    ('Aysel Babayeva', '+994514567890', 'aysel@mail.com', 6, 5, now + timedelta(days=1, hours=3), 'confirmed', 'Vegetarian options required'),
    ('Mehmet Yilmaz', '+994555678901', '', 8, 6, now + timedelta(days=2), 'pending', 'High chair needed'),
]
for cname, phone, email, table_num, guests, res_date, res_status, req in reservations_data:
    Reservation.objects.get_or_create(
        customer_name=cname, reservation_date=res_date,
        defaults={
            'customer_phone': phone, 'customer_email': email,
            'table': tables[table_num], 'guest_count': guests,
            'status': res_status, 'special_requests': req,
            'created_by': staff_users[0]
        }
    )

# Active orders for occupied table
order1, created = Order.objects.get_or_create(
    table=tables[3], status='preparing',
    defaults={
        'order_type': 'dine_in', 'server': staff_users[0],
        'payment_status': 'unpaid', 'customer_name': 'Table 3 Customer'
    }
)
if created:
    for item_name, qty in [('Bruschetta al Pomodoro', 2), ('Caesar Salad', 1), ('Ribeye Steak 300g', 2), ('House Red Wine (glass)', 2)]:
        mi = menu_objects[item_name]
        OrderItem.objects.create(order=order1, menu_item=mi, quantity=qty, unit_price=mi.price)

# Completed paid order (for reports)
order2, created = Order.objects.get_or_create(
    table=tables[1], status='completed',
    defaults={
        'order_type': 'dine_in', 'server': staff_users[1],
        'payment_status': 'paid', 'payment_method': 'card'
    }
)
if created:
    for item_name, qty in [('Hummus & Pita', 1), ('Chicken Schnitzel', 2), ('Tiramisu', 2), ('Espresso', 2)]:
        mi = menu_objects[item_name]
        OrderItem.objects.create(order=order2, menu_item=mi, quantity=qty, unit_price=mi.price)

# Takeaway order
order3, created = Order.objects.get_or_create(
    customer_name='Kamran Aliyev', order_type='takeaway', status='ready',
    defaults={
        'server': staff_users[0], 'payment_status': 'paid', 'payment_method': 'online'
    }
)
if created:
    for item_name, qty in [('Mixed Kebab Platter', 1), ('Fresh Orange Juice', 2)]:
        mi = menu_objects[item_name]
        OrderItem.objects.create(order=order3, menu_item=mi, quantity=qty, unit_price=mi.price)

# Inventory
inventory_data = [
    ('Chicken Breast', 'kg', 15.5, 5, 8.50, 'Fresh Farm Co.'),
    ('Beef (Ribeye)', 'kg', 8.0, 3, 22.00, 'Premium Meats Ltd.'),
    ('Lamb Chops', 'kg', 6.5, 3, 18.00, 'Premium Meats Ltd.'),
    ('Sea Bass (whole)', 'kg', 4.0, 2, 14.00, 'Caspian Seafood'),
    ('Pasta (Spaghetti)', 'kg', 12.0, 5, 1.50, 'Italian Foods Import'),
    ('Arborio Rice', 'kg', 8.0, 3, 2.00, 'Italian Foods Import'),
    ('Olive Oil', 'l', 9.5, 3, 7.00, 'Mediterranean Imports'),
    ('Heavy Cream', 'l', 3.5, 2, 3.50, 'Local Dairy'),
    ('Parmesan Cheese', 'kg', 2.0, 1, 18.00, 'Cheese World'),  # LOW STOCK
    ('Eggs', 'pcs', 80, 30, 0.25, 'Local Farm'),
    ('Lemons', 'pcs', 45, 20, 0.30, 'Green Market'),
    ('Tomatoes', 'kg', 9.0, 4, 2.00, 'Green Market'),
    ('Lettuce (Romaine)', 'pcs', 8, 5, 1.20, 'Green Market'),
    ('Flour (00)', 'kg', 20.0, 8, 0.90, 'Bakery Supplies'),
    ('Sugar', 'kg', 5.0, 3, 0.80, 'Bulk Foods'),  # approaching threshold
    ('Butter', 'kg', 2.5, 2, 6.00, 'Local Dairy'),  # LOW STOCK
    ('Red Wine (house)', 'l', 18.0, 6, 5.00, 'Wine Imports AZ'),
    ('Orange Juice (fresh)', 'l', 8.0, 4, 2.50, 'Juice Factory'),
    ('Coffee Beans', 'kg', 3.5, 2, 12.00, 'Coffee Masters'),  # LOW STOCK
    ('Mushrooms (porcini)', 'kg', 1.2, 1, 25.00, 'Specialty Foods'),  # LOW STOCK
]
for name, unit, qty, min_t, cost, supplier in inventory_data:
    InventoryItem.objects.get_or_create(name=name, defaults={
        'unit': unit, 'quantity': qty, 'min_threshold': min_t,
        'cost_per_unit': cost, 'supplier': supplier,
        'last_restocked': timezone.now() - timezone.timedelta(days=3)
    })

print("✅ Done! Created:")
print(f"   {Category.objects.count()} categories")
print(f"   {MenuItem.objects.count()} menu items")
print(f"   {Table.objects.count()} tables")
print(f"   {Reservation.objects.count()} reservations")
print(f"   {Order.objects.count()} orders")
print(f"   {InventoryItem.objects.count()} inventory items")
low = sum(1 for i in InventoryItem.objects.all() if i.is_low_stock)
print(f"   {low} low-stock alerts")
print("\nAdmin login: admin / admin123")
print("Staff login: waiter1 / password123")
