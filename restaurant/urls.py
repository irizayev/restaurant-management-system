from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/login/', views.LoginView.as_view(), name='login'),

    # Menu
    path('menu/', views.FullMenuView.as_view(), name='full-menu'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('menu-items/', views.MenuItemListView.as_view(), name='menuitem-list'),
    path('menu-items/<int:pk>/', views.MenuItemDetailView.as_view(), name='menuitem-detail'),

    # Tables
    path('tables/', views.TableListView.as_view(), name='table-list'),
    path('tables/availability/', views.table_availability, name='table-availability'),
    path('tables/<int:pk>/', views.TableDetailView.as_view(), name='table-detail'),
    path('tables/<int:pk>/status/', views.UpdateTableStatusView.as_view(), name='table-status'),

    # Reservations
    path('reservations/', views.ReservationListView.as_view(), name='reservation-list'),
    path('reservations/<int:pk>/', views.ReservationDetailView.as_view(), name='reservation-detail'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/status/', views.UpdateOrderStatusView.as_view(), name='order-status'),
    path('orders/<int:pk>/pay/', views.ProcessPaymentView.as_view(), name='order-pay'),

    # Inventory
    path('inventory/', views.InventoryListView.as_view(), name='inventory-list'),
    path('inventory/<int:pk>/', views.InventoryDetailView.as_view(), name='inventory-detail'),
    path('inventory/<int:pk>/restock/', views.RestockInventoryView.as_view(), name='inventory-restock'),

    # Reports & Dashboard
    path('reports/daily-sales/', views.daily_sales_report, name='daily-sales'),
    path('reports/stock-alerts/', views.stock_alerts, name='stock-alerts'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
