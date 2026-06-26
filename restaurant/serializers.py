from rest_framework import serializers
from .models import Category, MenuItem, Table, Reservation, Order, OrderItem, InventoryItem


class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'item_count']

    def get_item_count(self, obj):
        return obj.items.filter(is_available=True).count()


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'category', 'category_name',
            'is_available', 'is_vegetarian', 'is_vegan', 'is_gluten_free',
            'preparation_time', 'calories', 'image_url', 'created_at'
        ]


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = '__all__'


class ReservationSerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(source='table.number', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id', 'customer_name', 'customer_phone', 'customer_email',
            'table', 'table_number', 'guest_count', 'reservation_date',
            'status', 'special_requests', 'created_at'
        ]

    def validate(self, attrs):
        table = attrs.get('table')
        guest_count = attrs.get('guest_count')
        reservation_date = attrs.get('reservation_date')

        if table and guest_count and guest_count > table.capacity:
            raise serializers.ValidationError(
                f"Table #{table.number} only seats {table.capacity} guests, but {guest_count} requested."
            )

        from django.utils import timezone
        if reservation_date and reservation_date < timezone.now():
            raise serializers.ValidationError({'reservation_date': 'Cannot book a table in the past.'})

        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'quantity', 'unit_price', 'special_requests', 'line_total']
        read_only_fields = ['unit_price']

    def validate_menu_item(self, value):
        if not value.is_available:
            raise serializers.ValidationError(f"'{value.name}' is currently not available.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    table_number = serializers.IntegerField(source='table.number', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'table', 'table_number', 'server', 'status', 'order_type',
            'customer_name', 'payment_status', 'payment_method',
            'notes', 'discount', 'items', 'subtotal', 'discount_amount',
            'total', 'item_count', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            menu_item = item_data['menu_item']
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=item_data['quantity'],
                unit_price=menu_item.price,
                special_requests=item_data.get('special_requests', '')
            )
        # Mark table as occupied
        if order.table and order.order_type == 'dine_in':
            order.table.status = 'occupied'
            order.table.save()
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                menu_item = item_data['menu_item']
                OrderItem.objects.create(
                    order=instance,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    unit_price=menu_item.price,
                    special_requests=item_data.get('special_requests', '')
                )
        return instance


class InventoryItemSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InventoryItem
        fields = '__all__'
