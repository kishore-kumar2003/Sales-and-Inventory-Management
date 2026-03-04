# Manufacturing Sales & Inventory Management System - Test Cases & Workflows

## 🧪 Test Workflow

### Step 1: Authentication Setup

#### 1.1 Register a Sales User
```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sales@example.com",
    "name": "John Sales",
    "password": "secure123",
    "role": "SALES"
  }'
```

#### 1.2 Login to Get Token
```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sales@example.com",
    "password": "secure123"
  }'
```
**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```
Store the `access` token for API calls.

---

### Step 2: Product Setup

#### 2.1 Create Products
```bash
# Product 1: Widget A
curl -X POST http://localhost:8000/api/core/products/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget A",
    "description": "Premium grade widget",
    "cost_price": 100.00,
    "selling_price": 150.00,
    "minimum_stock": 50,
    "current_stock": 0,
    "is_active": true
  }'

# Product 2: Widget B
curl -X POST http://localhost:8000/api/core/products/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget B",
    "description": "Standard grade widget",
    "cost_price": 75.00,
    "selling_price": 120.00,
    "minimum_stock": 30,
    "current_stock": 0,
    "is_active": true
  }'
```

#### 2.2 Verify Product Creation
```bash
curl -X GET http://localhost:8000/api/core/products/ \
  -H "Authorization: Bearer <access_token>"
```

---

### Step 3: Production Records

#### 3.1 Register Production Activity
```bash
# Manufacturing batch 001 - Widget A
curl -X POST http://localhost:8000/api/core/productions/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product": 1,
    "quantity_produced": 200,
    "production_date": "2024-03-01",
    "notes": "Batch 001 - Quality checked"
  }'

# Manufacturing batch 002 - Widget B
curl -X POST http://localhost:8000/api/core/productions/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product": 2,
    "quantity_produced": 150,
    "production_date": "2024-03-01",
    "notes": "Batch 002 - Standard production"
  }'
```

#### 3.2 Verify Stock Updated
```bash
# Widget A should now have 200 units
curl -X GET http://localhost:8000/api/core/products/1/ \
  -H "Authorization: Bearer <access_token>"

# Widget B should now have 150 units
curl -X GET http://localhost:8000/api/core/products/2/ \
  -H "Authorization: Bearer <access_token>"
```

---

### Step 4: Sales Transactions

#### 4.1 Create First Sale
```bash
curl -X POST http://localhost:8000/api/core/sales/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2024-001",
    "customer_name": "ABC Manufacturing Ltd",
    "sale_date": "2024-03-02",
    "notes": "Regular monthly order",
    "items": [
      {
        "product": 1,
        "quantity_sold": 25,
        "unit_price": 150.00,
        "discount": 5
      },
      {
        "product": 2,
        "quantity_sold": 10,
        "unit_price": 120.00,
        "discount": 0
      }
    ]
  }'
```

**Expected Results:**
- Widget A stock: 200 - 25 = 175
- Widget B stock: 150 - 10 = 140
- Invoice total: (25×150×0.95) + (10×120) = 3570 + 1200 = 4770

#### 4.2 Create Second Sale
```bash
curl -X POST http://localhost:8000/api/core/sales/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2024-002",
    "customer_name": "XYZ Industries",
    "sale_date": "2024-03-02",
    "notes": "Bulk order",
    "items": [
      {
        "product": 1,
        "quantity_sold": 50,
        "unit_price": 150.00,
        "discount": 10
      }
    ]
  }'
```

**Expected Results:**
- Widget A stock: 175 - 50 = 125
- Invoice total: 50×150×0.9 = 6750

#### 4.3 Create Third Sale
```bash
curl -X POST http://localhost:8000/api/core/sales/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2024-003",
    "customer_name": "PQR Corp",
    "sale_date": "2024-03-03",
    "notes": "Widget B order",
    "items": [
      {
        "product": 2,
        "quantity_sold": 60,
        "unit_price": 120.00,
        "discount": 8
      }
    ]
  }'
```

---

### Step 5: Stock Validation

#### 5.1 Check Current Stock
```bash
curl -X GET http://localhost:8000/api/core/products/stock_summary/ \
  -H "Authorization: Bearer <access_token>"
```

**Expected Response:**
```json
{
  "total_products": 2,
  "low_stock_count": 1,
  "total_stock_value": 19625,
  "total_products_value": 31200
}
```

#### 5.2 Check Low Stock Alerts
```bash
curl -X GET http://localhost:8000/api/core/products/low_stock_alerts/ \
  -H "Authorization: Bearer <access_token>"
```

**Explanation:** Widget B has 80 units but minimum_stock is 30, so no alert.
Widget A has 125 units but minimum_stock is 50, so no alert.

---

### Step 6: Analytics & Reports

#### 6.1 Monthly Sales Report
```bash
curl -X GET "http://localhost:8000/api/core/sales/monthly_report/?month=3&year=2024" \
  -H "Authorization: Bearer <access_token>"
```

**Expected Response:**
```json
{
  "month": 3,
  "year": 2024,
  "total_sales_count": 3,
  "total_revenue": 15020,
  "average_sale_value": 5006.67,
  "best_selling_products": [
    {
      "product__name": "Widget A",
      "quantity": 75,
      "revenue": 10500
    },
    {
      "product__name": "Widget B",
      "quantity": 70,
      "revenue": 8064
    }
  ],
  "top_sales_staff": [
    {
      "sold_by__name": "John Sales",
      "total_sales": 3,
      "total_amount": 15020
    }
  ]
}
```

#### 6.2 Best Selling Products
```bash
curl -X GET "http://localhost:8000/api/core/sales/best_selling_products/?limit=10&days=30" \
  -H "Authorization: Bearer <access_token>"
```

#### 6.3 Product-wise Sales Analysis
```bash
curl -X GET "http://localhost:8000/api/core/sales/product_wise_sales/?product_id=1" \
  -H "Authorization: Bearer <access_token>"
```

**Expected Response:**
```json
{
  "total_quantity_sold": 75,
  "total_revenue": 10500,
  "number_of_transactions": 2
}
```

#### 6.4 Stock History for Product
```bash
curl -X GET http://localhost:8000/api/core/products/1/stock_history/ \
  -H "Authorization: Bearer <access_token>"
```

**Expected Response:** List of all stock changes:
```json
[
  {
    "id": 3,
    "product": 1,
    "transaction_type": "SALE",
    "quantity_change": -50,
    "previous_quantity": 175,
    "new_quantity": 125,
    "created_at": "2024-03-02T14:30:00Z"
  },
  {
    "id": 2,
    "product": 1,
    "transaction_type": "SALE",
    "quantity_change": -25,
    "previous_quantity": 200,
    "new_quantity": 175,
    "created_at": "2024-03-02T12:15:00Z"
  },
  {
    "id": 1,
    "product": 1,
    "transaction_type": "PRODUCTION",
    "quantity_change": 200,
    "previous_quantity": 0,
    "new_quantity": 200,
    "created_at": "2024-03-01T09:00:00Z"
  }
]
```

---

### Step 7: Production Summary

#### 7.1 Monthly Production Summary
```bash
curl -X GET "http://localhost:8000/api/core/productions/monthly_summary/?month=3&year=2024" \
  -H "Authorization: Bearer <access_token>"
```

**Expected Response:**
```json
{
  "total_quantity": 350,
  "total_productions": 2,
  "products": [
    {
      "product__name": "Widget A",
      "total_quantity": 200,
      "count": 1
    },
    {
      "product__name": "Widget B",
      "total_quantity": 150,
      "count": 1
    }
  ]
}
```

---

### Step 8: Error Handling

#### 8.1 Attempt Over-selling
```bash
# Try to sell 200 units of Widget A when only 125 are in stock
curl -X POST http://localhost:8000/api/core/sales/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2024-004",
    "customer_name": "Test Corp",
    "sale_date": "2024-03-03",
    "items": [
      {
        "product": 1,
        "quantity_sold": 200,
        "unit_price": 150.00,
        "discount": 0
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "error": "Insufficient stock. Available: 125"
}
```

#### 8.2 Duplicate Invoice Number
```bash
# Try to create sale with existing invoice number
curl -X POST http://localhost:8000/api/core/sales/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2024-001",
    "customer_name": "Duplicate Corp",
    "sale_date": "2024-03-03",
    "items": [
      {
        "product": 1,
        "quantity_sold": 5,
        "unit_price": 150.00,
        "discount": 0
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "invoice_number": ["invoice number already exists"]
}
```

---

## 📈 Expected Data After Workflow

### Stock Levels
- Widget A: 125 units (out of 200 produced)
- Widget B: 80 units (out of 150 produced)

### Sales Summary
- Total Invoices: 3
- Total Revenue: 15,020
- Total Items Sold: 145 units

### Financial Summary
- Total Cost of Goods Sold: ~10,945
- Gross Profit: ~4,075
- Average Profit Margin: ~27%

---

## 🔍 Verification Queries

```bash
# List all sales with details
curl -X GET http://localhost:8000/api/core/sales/ \
  -H "Authorization: Bearer <access_token>"

# Get complete production history
curl -X GET http://localhost:8000/api/core/productions/ \
  -H "Authorization: Bearer <access_token>"

# View all stock transaction history
curl -X GET http://localhost:8000/api/core/stock-history/ \
  -H "Authorization: Bearer <access_token>"

# Check products with low stock
curl -X GET http://localhost:8000/api/core/products/low_stock_alerts/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 💡 Tips for Testing

1. **Use Thunder Client or Postman**: For easier API testing with UI
2. **Save Token**: Store JWT token for multiple requests
3. **Date Format**: Always use YYYY-MM-DD format for dates
4. **Decimal Places**: Use 2 decimal places for prices
5. **Unique Invoices**: Generate unique invoice numbers (INV-YYYY-MM-DD-001)
6. **Role Testing**: Create different user roles and test access restrictions

---

## 🚨 Edge Cases to Test

1. ✅ Selling more than available stock
2. ✅ Creating sale with 0 discount vs percentage discount
3. ✅ Production of 0 units (should validate)
4. ✅ Same invoice number twice (should fail)
5. ✅ Negative prices (validators prevent this)
6. ✅ Empty sale items list
7. ✅ Unauthorized user accessing admin data
8. ✅ Invalid date formats
