from django.contrib import admin
from .models import Category, MenuItem, Table, Reservation, Order, OrderItem, InventoryItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['line_total', 'unit_price']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'is_vegetarian', 'preparation_time']
    list_filter = ['category', 'is_available', 'is_vegetarian', 'is_vegan']
    search_fields = ['name', 'description']
    list_editable = ['is_available', 'price']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'capacity', 'status', 'location']
    list_filter = ['status', 'location']
    list_editable = ['status']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'customer_phone', 'table', 'guest_count', 'reservation_date', 'status']
    list_filter = ['status', 'reservation_date']
    search_fields = ['customer_name', 'customer_phone']
    date_hierarchy = 'reservation_date'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'table', 'status', 'order_type', 'payment_status', 'total', 'created_at']
    list_filter = ['status', 'order_type', 'payment_status']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']

    def total(self, obj):
        return f"${obj.total:.2f}"


@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'unit', 'min_threshold', 'is_low_stock', 'supplier', 'last_restocked']
    list_filter = ['unit']
    search_fields = ['name', 'supplier']

    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock?'
