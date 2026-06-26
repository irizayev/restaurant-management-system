from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    is_available = models.BooleanField(default=True)
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    preparation_time = models.PositiveIntegerField(default=15)
    calories = models.PositiveIntegerField(null=True, blank=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (${self.price})"


TABLE_STATUS = [
    ('available', 'Available'),
    ('occupied', 'Occupied'),
    ('reserved', 'Reserved'),
    ('cleaning', 'Cleaning'),
]

RES_STATUS = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('seated', 'Seated'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('no_show', 'No Show'),
]

ORDER_STATUS = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('preparing', 'Preparing'),
    ('ready', 'Ready'),
    ('served', 'Served'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

ORDER_TYPE = [
    ('dine_in', 'Dine In'),
    ('takeaway', 'Takeaway'),
    ('delivery', 'Delivery'),
]

PAY_STATUS = [
    ('unpaid', 'Unpaid'),
    ('paid', 'Paid'),
    ('refunded', 'Refunded'),
]

PAY_METHOD = [
    ('cash', 'Cash'),
    ('card', 'Card'),
    ('online', 'Online'),
]

UNIT_CHOICES = [
    ('kg', 'Kilograms'),
    ('g', 'Grams'),
    ('l', 'Liters'),
    ('ml', 'Milliliters'),
    ('pcs', 'Pieces'),
    ('box', 'Box'),
]


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=TABLE_STATUS, default='available')
    location = models.CharField(max_length=100, default='Main Hall')

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Table #{self.number} ({self.capacity} seats) - {self.status}"


class Reservation(models.Model):
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, related_name='reservations')
    guest_count = models.PositiveIntegerField()
    reservation_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=RES_STATUS, default='pending')
    special_requests = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['reservation_date']

    def __str__(self):
        return f"{self.customer_name} - Table #{self.table.number if self.table else '?'}"


class Order(models.Model):
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    server = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='served_orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE, default='dine_in')
    customer_name = models.CharField(max_length=200, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAY_STATUS, default='unpaid')
    payment_method = models.CharField(max_length=20, choices=PAY_METHOD, null=True, blank=True)
    notes = models.TextField(blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def discount_amount(self):
        return (self.subtotal * self.discount) / 100

    @property
    def total(self):
        return self.subtotal - self.discount_amount

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    special_requests = models.CharField(max_length=300, blank=True)

    class Meta:
        unique_together = ('order', 'menu_item')

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.menu_item.price
        super().save(*args, **kwargs)


class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    cost_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    supplier = models.CharField(max_length=200, blank=True)
    last_restocked = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_threshold

    @property
    def stock_value(self):
        return self.quantity * self.cost_per_unit
