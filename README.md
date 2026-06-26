# Task 3 — Restaurant Management System
> Django REST Framework backend | CodeAlpha Internship

## Tech Stack
- **Python 3** / **Django 4** / **Django REST Framework**
- **SQLite** (dev) — swap to PostgreSQL in production
- Token-based authentication

## Quick Start

```bash
# 1. Install dependencies
pip install django djangorestframework django-cors-headers django-filter

# 2. Apply migrations
python manage.py migrate

# 3. Seed sample data (7 categories, 23 menu items, 10 tables, etc.)
python seed_data.py

# 4. Run server
python manage.py runserver
```

Admin: `http://127.0.0.1:8000/admin/` — `admin` / `admin123`

---

## API Endpoints

### Auth
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/login/` | Get auth token |

### Menu
| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/api/menu/` | Full menu grouped by category |
| GET  | `/api/menu-items/` | All items (filterable) |
| GET  | `/api/menu-items/?category=1` | By category |
| GET  | `/api/menu-items/?available=true` | Available only |
| GET  | `/api/menu-items/?vegetarian=true` | Vegetarian only |
| GET  | `/api/menu-items/?search=steak` | Search |
| POST | `/api/menu-items/` | Add item (auth) |
| PUT/PATCH/DELETE | `/api/menu-items/<id>/` | Update/delete (auth) |
| GET/POST | `/api/categories/` | Category list/create |

### Tables
| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/api/tables/` | All tables |
| GET  | `/api/tables/?status=available` | Filter by status |
| GET  | `/api/tables/availability/` | Availability summary |
| POST | `/api/tables/` | Add table (auth) |
| PATCH | `/api/tables/<id>/status/` | Update status (auth) |

### Reservations
| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/api/reservations/` | All reservations (auth) |
| GET  | `/api/reservations/?date=2026-06-28` | By date |
| GET  | `/api/reservations/?status=confirmed` | By status |
| POST | `/api/reservations/` | Create reservation (auth) |
| PUT/PATCH | `/api/reservations/<id>/` | Update (auto-updates table) |
| DELETE | `/api/reservations/<id>/` | Cancel |

### Orders
| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/api/orders/` | All orders (auth) |
| GET  | `/api/orders/?status=preparing` | Filter by status |
| GET  | `/api/orders/?order_type=takeaway` | Filter by type |
| POST | `/api/orders/` | Place order (auth) |
| GET  | `/api/orders/<id>/` | Order detail with items |
| PATCH | `/api/orders/<id>/status/` | Update status |
| POST | `/api/orders/<id>/pay/` | Process payment |

### Inventory
| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/api/inventory/` | Full inventory list (auth) |
| GET  | `/api/inventory/?low_stock=true` | Low stock alerts |
| POST | `/api/inventory/` | Add item (auth) |
| PATCH | `/api/inventory/<id>/` | Update (auth) |
| POST | `/api/inventory/<id>/restock/` | Restock item (auth) |

### Reports & Dashboard
| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/api/dashboard/` | KPI summary (auth) |
| GET  | `/api/reports/daily-sales/` | Daily sales report (auth) |
| GET  | `/api/reports/daily-sales/?date=2026-06-27` | For specific date |
| GET  | `/api/reports/stock-alerts/` | Low-stock items (auth) |

---

## Example Usage

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"waiter1","password":"password123"}'
```

### View full menu
```bash
curl http://127.0.0.1:8000/api/menu/
```

### Place an order
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "table": 3,
    "order_type": "dine_in",
    "items": [
      {"menu_item": 1, "quantity": 2},
      {"menu_item": 5, "quantity": 1}
    ]
  }'
```

### Update order status (kitchen flow)
```bash
# pending → confirmed → preparing → ready → served → completed
curl -X PATCH http://127.0.0.1:8000/api/orders/1/status/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "preparing"}'
```

### Process payment
```bash
curl -X POST http://127.0.0.1:8000/api/orders/1/pay/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"payment_method": "card"}'
```

### Restock inventory
```bash
curl -X POST http://127.0.0.1:8000/api/inventory/1/restock/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10}'
```

### Dashboard KPIs
```bash
curl -H "Authorization: Token <token>" http://127.0.0.1:8000/api/dashboard/
```

---

## Models

### Category / MenuItem
- Full menu with categories, dietary flags (vegetarian/vegan/gluten-free), prep time, calories

### Table
- Status: `available` → `reserved` → `occupied` → `cleaning` → `available`
- Auto-updated when orders complete or reservations change

### Reservation
- Customer info, guest count, table, date/time
- Status flow: `pending → confirmed → seated → completed`
- Validates table capacity and future date

### Order / OrderItem
- Types: dine-in, takeaway, delivery
- Status flow: `pending → confirmed → preparing → ready → served → completed`
- Price snapshot on order items (preserves historical pricing)
- Auto calculates subtotal, discount, total

### InventoryItem
- Quantity tracking with low-stock threshold alerts
- Restocking API with timestamp
- Stock value calculation

---

## Test Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Waiter/Staff | `waiter1` | `password123` |
| Manager | `manager1` | `password123` |
