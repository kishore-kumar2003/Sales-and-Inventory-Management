# Manufacturing Sales & Inventory Management System - API Documentation

## Base URL
```
http://localhost:8000/api
```

---

## 📌 Authentication Endpoints

### 1. User Registration
**POST** `/accounts/register/`
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "password123",
  "role": "SALES"
}
```
**Response:** User created successfully
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "SALES"
}
```

### 2. Login
**POST** `/accounts/login/`
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 3. Refresh Token
**POST** `/accounts/refresh/`
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 4. Get All Users
**GET** `/accounts/users/`
```
Headers: Authorization: Bearer <access_token>
```

---

## 📦 Product Management Endpoints

### 1. Create Product
**POST** `/core/products/`
```json
{
  "name": "Widget A",
  "description": "Premium widget for manufacturing",
  "cost_price": 100.00,
  "selling_price": 150.00,
  "minimum_stock": 50,
  "current_stock": 100,
  "is_active": true
}
```

### 2. Get All Products
**GET** `/core/products/`

### 3. Get Single Product
**GET** `/core/products/{id}/`

### 4. Update Product
**PUT** `/core/products/{id}/`
```json
{
  "name": "Widget A",
  "cost_price": 105.00,
  "selling_price": 155.00,
  "minimum_stock": 60
}
```

### 5. Delete Product
**DELETE** `/core/products/{id}/`

### 6. Get Low Stock Alert
**GET** `/core/products/low_stock_alerts/`
Returns all products with stock ≤ minimum_stock

### 7. Get Stock Summary
**GET** `/core/products/stock_summary/`
Returns:
- Total products
- Low stock count
- Total stock value (cost price)
- Total products value (selling price)

### 8. Get Product Stock History
**GET** `/core/products/{id}/stock_history/`
Returns last 50 stock transactions for the product

---

## 🏭 Production Management Endpoints

### 1. Record Production
**POST** `/core/productions/`
```json
{
  "product": 1,
  "quantity_produced": 50,
  "production_date": "2024-03-03",
  "notes": "Batch 001"
}
```
**Auto-updates product stock**

### 2. Get All Productions
**GET** `/core/productions/`

### 3. Get Production by Product
**GET** `/core/productions/by_product/?product_id=1`

### 4. Get Production in Date Range
**GET** `/core/productions/date_range/?start_date=2024-01-01&end_date=2024-03-03`

### 5. Get Monthly Production Summary
**GET** `/core/productions/monthly_summary/?month=3&year=2024`
Returns:
- Total quantity produced
- Total productions count
- Product-wise breakdown

---

## 🧾 Sales Management Endpoints

### 1. Create Sale (with items)
**POST** `/core/sales/`
```json
{
  "invoice_number": "INV-001",
  "customer_name": "ABC Corporation",
  "sale_date": "2024-03-03",
  "notes": "Regular order",
  "items": [
    {
      "product": 1,
      "quantity_sold": 10,
      "unit_price": 150.00,
      "discount": 5
    },
    {
      "product": 2,
      "quantity_sold": 20,
      "unit_price": 200.00,
      "discount": 0
    }
  ]
}
```
**Auto-reduces product stock and calculates total**

### 2. Get All Sales
**GET** `/core/sales/`
*(Users see only their sales; Admins see all)*

### 3. Get Sale Details
**GET** `/core/sales/{id}/`
Includes all sale items

### 4. Get Sales by Staff
**GET** `/core/sales/by_staff/?staff_id=1`
Returns:
- Total sales count
- Total amount
- List of sales

### 5. Get Sales in Date Range
**GET** `/core/sales/date_range/?start_date=2024-01-01&end_date=2024-03-03`
Returns summary and list

### 6. Get Product-wise Sales
**GET** `/core/sales/product_wise_sales/?product_id=1`
Returns:
- Total quantity sold
- Total revenue
- Number of transactions

### 7. Get Monthly Sales Report
**GET** `/core/sales/monthly_report/?month=3&year=2024`
Returns:
- Total sales count
- Total revenue
- Average sale value
- Top 5 best-selling products
- Top 5 sales staff members

### 8. Get Best Selling Products
**GET** `/core/sales/best_selling_products/?limit=10&days=30`
Returns top products by quantity

### 9. Get Slow Moving Products
**GET** `/core/sales/slow_moving_products/?limit=10&days=90`
Returns products with lowest sales

---

## 📊 Stock History Endpoints

### 1. Get All Stock History
**GET** `/core/stock-history/`

### 2. Get Stock History by Product
**GET** `/core/stock-history/by_product/?product_id=1`

### 3. Get Stock History by Transaction Type
**GET** `/core/stock-history/by_transaction_type/?type=PRODUCTION`
Types: `PRODUCTION`, `SALE`, `ADJUSTMENT`

---

## 📈 Key API Features

### Role-Based Access Control
- **ADMIN**: Full access to all data
- **SALES**: Can create sales, view own sales
- **PRODUCTION**: Can create production records
- **ACCOUNTANT**: View-only access to reports
- **STORE**: Can view inventory and manage stock

### Business Rules Implemented
✅ Stock never goes negative  
✅ Production auto-increases stock  
✅ Sales auto-decrease stock  
✅ Invoice numbers are unique  
✅ Low stock alerts (≤ minimum_stock)  
✅ Automatic profit margin calculation  

### Response Format
All successful responses return HTTP 200/201:
```json
{
  "id": 1,
  "field": "value",
  "created_at": "2024-03-03T10:30:00Z"
}
```

### Error Response Format
```json
{
  "error": "descriptive error message"
}
```

---

## 🔐 Authentication Header
All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

---

## 📝 Example Workflow

1. **Register User**
   - POST `/accounts/register/`

2. **Login**
   - POST `/accounts/login/` → Get access_token

3. **Create Product**
   - POST `/core/products/` (requires authentication)

4. **Record Production**
   - POST `/core/productions/` → Stock increases

5. **Create Sale**
   - POST `/core/sales/` → Stock decreases

6. **View Reports**
   - GET `/core/sales/monthly_report/?month=3&year=2024`
   - GET `/core/sales/best_selling_products/`
   - GET `/core/products/low_stock_alerts/`

---

## Database Models

### Product
- name, description, cost_price, selling_price
- minimum_stock, current_stock
- is_active, created_at, updated_at

### Production
- product (FK), quantity_produced
- produced_by (User FK), production_date
- notes, created_at

### Sale
- invoice_number (unique), customer_name
- sold_by (User FK), total_amount
- sale_date, notes, created_at, updated_at

### SaleItem
- sale (FK), product (FK)
- quantity_sold, unit_price, discount

### StockHistory
- product (FK), transaction_type
- quantity_change, previous_quantity, new_quantity
- reference_id, created_by (User FK), created_at
