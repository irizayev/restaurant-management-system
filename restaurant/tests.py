from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import timedelta
from .models import Category, MenuItem, Table, Reservation, Order, OrderItem, InventoryItem


def create_staff():
    user = User.objects.create_user(username='staff', password='pass1234', is_staff=True)
    token = Token.objects.create(user=user)
    return user, token


class MenuTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff, self.token = create_staff()
        self.category = Category.objects.create(name='Starters', description='Appetizers')
        self.item = MenuItem.objects.create(
            name='Hummus', description='Creamy chickpea dip', price=6.50,
            category=self.category, is_available=True, is_vegan=True,
            preparation_time=10, calories=280,
        )

    def test_full_menu_public(self):
        response = self.client.get('/api/menu/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], 'Starters')

    def test_list_menu_items(self):
        response = self.client.get('/api/menu-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_vegan_items(self):
        response = self.client.get('/api/menu-items/?vegan=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_search_menu_items(self):
        response = self.client.get('/api/menu-items/?search=Hummus')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['count'], 0)

    def test_create_menu_item_requires_auth(self):
        response = self.client.post('/api/menu-items/', {'name': 'Test', 'price': 5.00})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_menu_item_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post('/api/menu-items/', {
            'name': 'New Dish', 'description': 'Tasty', 'price': 12.00,
            'category': self.category.id, 'preparation_time': 15, 'is_available': True,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_menu_item_detail(self):
        response = self.client.get(f'/api/menu-items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Hummus')


class TableTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff, self.token = create_staff()
        self.table = Table.objects.create(number=1, capacity=4, status='available', location='Main Hall')

    def test_list_tables_public(self):
        response = self.client.get('/api/tables/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_availability_summary(self):
        response = self.client.get('/api/tables/availability/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available', response.data)
        self.assertEqual(response.data['available'], 1)

    def test_filter_by_status(self):
        response = self.client.get('/api/tables/?status=available')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_update_table_status(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.patch(f'/api/tables/{self.table.id}/status/', {'status': 'occupied'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')

    def test_invalid_table_status(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.patch(f'/api/tables/{self.table.id}/status/', {'status': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReservationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff, self.token = create_staff()
        self.table = Table.objects.create(number=2, capacity=4, status='available', location='Terrace')

    def test_create_reservation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post('/api/reservations/', {
            'customer_name': 'John Doe',
            'customer_phone': '+994501234567',
            'table': self.table.id,
            'guest_count': 3,
            'reservation_date': (timezone.now() + timedelta(hours=3)).isoformat(),
            'status': 'confirmed',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'reserved')

    def test_reservation_exceeds_capacity(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post('/api/reservations/', {
            'customer_name': 'John Doe',
            'customer_phone': '+994501234567',
            'table': self.table.id,
            'guest_count': 10,  # Table only seats 4
            'reservation_date': (timezone.now() + timedelta(hours=3)).isoformat(),
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reservation_past_date(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post('/api/reservations/', {
            'customer_name': 'John Doe',
            'customer_phone': '+994501234567',
            'table': self.table.id,
            'guest_count': 2,
            'reservation_date': (timezone.now() - timedelta(hours=1)).isoformat(),
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff, self.token = create_staff()
        self.table = Table.objects.create(number=3, capacity=4, status='available', location='Main Hall')
        self.category = Category.objects.create(name='Mains')
        self.item1 = MenuItem.objects.create(
            name='Ribeye Steak', description='Premium beef', price=32.00,
            category=self.category, is_available=True, preparation_time=25,
        )
        self.item2 = MenuItem.objects.create(
            name='Caesar Salad', description='Fresh salad', price=9.00,
            category=self.category, is_available=True, preparation_time=8,
        )

    def test_place_order(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post('/api/orders/', {
            'table': self.table.id,
            'order_type': 'dine_in',
            'items': [
                {'menu_item': self.item1.id, 'quantity': 1},
                {'menu_item': self.item2.id, 'quantity': 2},
            ]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')

    def test_order_total_calculation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.client.post('/api/orders/', {
            'table': self.table.id,
            'order_type': 'dine_in',
            'items': [
                {'menu_item': self.item1.id, 'quantity': 1},
                {'menu_item': self.item2.id, 'quantity': 2},
            ]
        }, format='json')
        order = Order.objects.first()
        self.assertEqual(float(order.total), 32.00 + 9.00 * 2)

    def test_update_order_status(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        order = Order.objects.create(table=self.table, status='pending', order_type='dine_in', server=self.staff)
        response = self.client.patch(f'/api/orders/{order.id}/status/', {'status': 'preparing'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'preparing')

    def test_process_payment(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        order = Order.objects.create(table=self.table, status='served', order_type='dine_in', server=self.staff)
        response = self.client.post(f'/api/orders/{order.id}/pay/', {'payment_method': 'card'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')
        self.assertEqual(order.status, 'completed')
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'cleaning')

    def test_cannot_pay_twice(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        order = Order.objects.create(
            table=self.table, status='completed', order_type='dine_in',
            server=self.staff, payment_status='paid', payment_method='cash'
        )
        response = self.client.post(f'/api/orders/{order.id}/pay/', {'payment_method': 'card'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InventoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff, self.token = create_staff()
        self.item = InventoryItem.objects.create(
            name='Chicken Breast', unit='kg', quantity=15.0,
            min_threshold=5.0, cost_per_unit=8.50, supplier='Fresh Farm Co.',
        )
        self.low_item = InventoryItem.objects.create(
            name='Truffle Oil', unit='ml', quantity=50.0,
            min_threshold=100.0, cost_per_unit=25.00, supplier='Luxury Foods',
        )

    def test_list_inventory_requires_auth(self):
        response = self.client.get('/api/inventory/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_inventory(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_low_stock_filter(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/inventory/?low_stock=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [i['name'] for i in response.data['results']]
        self.assertIn('Truffle Oil', names)
        self.assertNotIn('Chicken Breast', names)

    def test_is_low_stock_property(self):
        self.assertFalse(self.item.is_low_stock)
        self.assertTrue(self.low_item.is_low_stock)

    def test_restock_item(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(f'/api/inventory/{self.item.id}/restock/', {'amount': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(float(self.item.quantity), 25.0)

    def test_restock_invalid_amount(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(f'/api/inventory/{self.item.id}/restock/', {'amount': -5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff, self.token = create_staff()

    def test_dashboard_requires_auth(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_returns_kpis(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ['orders_today', 'revenue_today', 'active_orders', 'tables_available']:
            self.assertIn(key, response.data)
