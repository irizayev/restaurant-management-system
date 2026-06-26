from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from .models import Category, MenuItem, Table, Reservation, Order, OrderItem, InventoryItem
from .serializers import (
    CategorySerializer, MenuItemSerializer, TableSerializer,
    ReservationSerializer, OrderSerializer, InventoryItemSerializer
)


# ─────────────────────────── AUTH ───────────────────────────

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'username': user.username, 'is_staff': user.is_staff})
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────── MENU ───────────────────────────

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class MenuItemListView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'preparation_time']

    def get_queryset(self):
        qs = MenuItem.objects.select_related('category')
        category = self.request.query_params.get('category')
        available = self.request.query_params.get('available')
        vegetarian = self.request.query_params.get('vegetarian')
        vegan = self.request.query_params.get('vegan')
        if category:
            qs = qs.filter(category_id=category)
        if available == 'true':
            qs = qs.filter(is_available=True)
        if vegetarian == 'true':
            qs = qs.filter(is_vegetarian=True)
        if vegan == 'true':
            qs = qs.filter(is_vegan=True)
        return qs


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class FullMenuView(APIView):
    """Returns entire menu grouped by category."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Category.objects.prefetch_related('items').all()
        result = []
        for cat in categories:
            items = cat.items.filter(is_available=True)
            if items.exists():
                result.append({
                    'category': cat.name,
                    'items': MenuItemSerializer(items, many=True).data
                })
        return Response(result)


# ─────────────────────────── TABLES ───────────────────────────

class TableListView(generics.ListCreateAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Table.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class TableDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]


class UpdateTableStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            table = Table.objects.get(pk=pk)
        except Table.DoesNotExist:
            return Response({'error': 'Table not found.'}, status=404)
        new_status = request.data.get('status')
        valid = ['available', 'occupied', 'reserved', 'cleaning']
        if new_status not in valid:
            return Response({'error': f'Invalid status. Choose from: {valid}'}, status=400)
        table.status = new_status
        table.save()
        return Response(TableSerializer(table).data)


# ─────────────────────────── RESERVATIONS ───────────────────────────

class ReservationListView(generics.ListCreateAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'customer_phone']
    ordering_fields = ['reservation_date', 'status']

    def get_queryset(self):
        qs = Reservation.objects.select_related('table')
        date = self.request.query_params.get('date')
        status_filter = self.request.query_params.get('status')
        if date:
            qs = qs.filter(reservation_date__date=date)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        reservation = serializer.save(created_by=self.request.user)
        if reservation.table:
            reservation.table.status = 'reserved'
            reservation.table.save()


class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        reservation = serializer.save()
        if reservation.status in ('cancelled', 'completed', 'no_show'):
            if reservation.table:
                reservation.table.status = 'available'
                reservation.table.save()
        elif reservation.status == 'seated':
            if reservation.table:
                reservation.table.status = 'occupied'
                reservation.table.save()


# ─────────────────────────── ORDERS ───────────────────────────

class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Order.objects.prefetch_related('items__menu_item').select_related('table', 'server')
        status_filter = self.request.query_params.get('status')
        order_type = self.request.query_params.get('order_type')
        payment = self.request.query_params.get('payment_status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if order_type:
            qs = qs.filter(order_type=order_type)
        if payment:
            qs = qs.filter(payment_status=payment)
        return qs

    def perform_create(self, serializer):
        serializer.save(server=self.request.user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.prefetch_related('items__menu_item').select_related('table')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]


class UpdateOrderStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=404)

        new_status = request.data.get('status')
        valid = ['pending', 'confirmed', 'preparing', 'ready', 'served', 'completed', 'cancelled']
        if new_status not in valid:
            return Response({'error': f'Choose from: {valid}'}, status=400)

        order.status = new_status
        # Auto free table when completed or cancelled
        if new_status in ('completed', 'cancelled') and order.table:
            order.table.status = 'cleaning' if new_status == 'completed' else 'available'
            order.table.save()
        order.save()
        return Response(OrderSerializer(order).data)


class ProcessPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=404)
        if order.payment_status == 'paid':
            return Response({'error': 'Order is already paid.'}, status=400)

        payment_method = request.data.get('payment_method', 'cash')
        order.payment_status = 'paid'
        order.payment_method = payment_method
        order.status = 'completed'
        if order.table:
            order.table.status = 'cleaning'
            order.table.save()
        order.save()
        return Response({
            'message': 'Payment processed successfully.',
            'order_id': order.id,
            'total': str(order.total),
            'payment_method': payment_method
        })


# ─────────────────────────── INVENTORY ───────────────────────────

class InventoryListView(generics.ListCreateAPIView):
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'supplier']

    def get_queryset(self):
        qs = InventoryItem.objects.all()
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            qs = [item for item in qs if item.is_low_stock]
        return qs if not isinstance(qs, list) else InventoryItem.objects.filter(
            id__in=[i.id for i in qs])


class InventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class RestockInventoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            item = InventoryItem.objects.get(pk=pk)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=404)
        amount = request.data.get('amount')
        if not amount or float(amount) <= 0:
            return Response({'error': 'Amount must be a positive number.'}, status=400)
        from decimal import Decimal
        item.quantity += Decimal(str(amount))
        item.last_restocked = timezone.now()
        item.save()
        return Response({
            'message': f'Restocked {item.name} by {amount} {item.unit}.',
            'new_quantity': item.quantity
        })


# ─────────────────────────── REPORTS ───────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def daily_sales_report(request):
    date_str = request.query_params.get('date')
    if date_str:
        from datetime import date
        target_date = date.fromisoformat(date_str)
    else:
        target_date = timezone.now().date()

    orders = Order.objects.filter(
        created_at__date=target_date,
        payment_status='paid'
    ).prefetch_related('items__menu_item')

    total_revenue = sum(o.total for o in orders)
    top_items = (
        OrderItem.objects
        .filter(order__in=orders)
        .values('menu_item__name')
        .annotate(qty=Sum('quantity'), revenue=Sum(F('quantity') * F('unit_price')))
        .order_by('-qty')[:5]
    )

    return Response({
        'date': str(target_date),
        'total_orders': orders.count(),
        'total_revenue': str(total_revenue),
        'orders_by_type': {
            'dine_in': orders.filter(order_type='dine_in').count(),
            'takeaway': orders.filter(order_type='takeaway').count(),
            'delivery': orders.filter(order_type='delivery').count(),
        },
        'top_items': list(top_items),
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def stock_alerts(request):
    low_items = [i for i in InventoryItem.objects.all() if i.is_low_stock]
    return Response({
        'alert_count': len(low_items),
        'items': InventoryItemSerializer(low_items, many=True).data
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def table_availability(request):
    tables = Table.objects.all()
    return Response({
        'total': tables.count(),
        'available': tables.filter(status='available').count(),
        'occupied': tables.filter(status='occupied').count(),
        'reserved': tables.filter(status='reserved').count(),
        'cleaning': tables.filter(status='cleaning').count(),
        'tables': TableSerializer(tables, many=True).data,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    today = timezone.now().date()
    paid_orders_today = Order.objects.filter(created_at__date=today, payment_status='paid')
    revenue_today = sum(o.total for o in paid_orders_today)
    low_stock_count = sum(1 for i in InventoryItem.objects.all() if i.is_low_stock)

    return Response({
        'today': str(today),
        'orders_today': Order.objects.filter(created_at__date=today).count(),
        'revenue_today': str(revenue_today),
        'active_orders': Order.objects.filter(status__in=['pending', 'confirmed', 'preparing', 'ready']).count(),
        'tables_available': Table.objects.filter(status='available').count(),
        'reservations_today': Reservation.objects.filter(reservation_date__date=today).count(),
        'low_stock_alerts': low_stock_count,
    })
