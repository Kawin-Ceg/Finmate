# FinMate — API Documentation

**Base URL:** `http://localhost:8000`  
**Authentication:** Bearer JWT (sent in `Authorization` header)  
**Content-Type:** `application/json` (except file upload which uses `multipart/form-data`)

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Transactions](#2-transactions)
3. [Analytics](#3-analytics)
4. [Budgets](#4-budgets)
5. [ML Model](#5-ml-model)
6. [Error Reference](#6-error-reference)

---

## 1. Authentication

Authentication endpoints do **not** require a Bearer token.

---

### `POST /auth/signup`

Create a new user account.

**Request Body**

```json
{
  "name": "Kawin Kumar",
  "email": "kawin@example.com",
  "password": "securepassword123"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|------------|
| `name` | string | Yes | Max 100 chars |
| `email` | string (EmailStr) | Yes | Valid email, unique |
| `password` | string | Yes | Plain text, bcrypt-hashed server-side |

**Response `200 OK`**

```json
{
  "message": "User created successfully"
}
```

**Error Responses**

| Status | Condition | Detail |
|--------|-----------|--------|
| `400` | Email already registered | `"Email already exists"` |
| `422` | Invalid email format or missing fields | Pydantic validation error |

---

### `POST /auth/login`

Authenticate an existing user and return a JWT access token.

**Request Body**

```json
{
  "email": "kawin@example.com",
  "password": "securepassword123"
}
```

**Response `200 OK`**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Kawin Kumar",
    "email": "kawin@example.com"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT token, valid for 24 hours |
| `token_type` | string | Always `"bearer"` |
| `user.id` | int | Unique user ID |
| `user.name` | string | Display name |
| `user.email` | string | Email address |

**Error Responses**

| Status | Condition | Detail |
|--------|-----------|--------|
| `401` | User not found | `"Invalid credentials"` |
| `401` | Wrong password | `"Invalid credentials"` |

**Usage Example**

```javascript
// Frontend (transactionService.js pattern)
const response = await api.post('/auth/login', { email, password });
localStorage.setItem('token', response.data.access_token);
localStorage.setItem('user', JSON.stringify(response.data.user));
```

---

## 2. Transactions

All transaction endpoints require a valid Bearer JWT token.

**Required Header:**
```
Authorization: Bearer <access_token>
```

---

### `POST /transactions/upload`

Upload a bank statement CSV file. Transactions are automatically parsed, categorized via the ML + rule-based hybrid engine, and stored in the database.

**Request:** `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `file` | File (.csv) | Yes |

**CSV Format Support**

The endpoint uses flexible column detection. Any of the following column names are recognized:

| Data | Accepted Column Names |
|------|----------------------|
| Date | `date`, `txn_date`, `transaction_date`, `value_date`, `posting_date` |
| Merchant | `merchant`, `payee`, `name`, `narration`, `particulars`, `description`, `details` |
| Description | `description`, `desc`, `remarks`, `note`, `reference` |
| Amount | `amount`, `transaction_amount`, `net_amount`, `txn_amount` |
| Debit | `debit`, `dr`, `withdrawal`, `withdrawn`, `debit_amount` |
| Credit | `credit`, `cr`, `deposit`, `deposited`, `credit_amount` |

**Supported Date Formats**

`dd/mm/yyyy`, `yyyy-mm-dd`, `dd-mm-yyyy`, `dd Mon yyyy`, `dd Month yyyy`, `mm/dd/yyyy`, `dd/mm/yy`, `yyyy/mm/dd`

**Supported Encodings:** `utf-8-sig`, `utf-8`, `latin-1` (auto-detected)

**Response `200 OK`**

```json
{
  "message": "Upload successful",
  "transactions_imported": 47
}
```

**Error Responses**

| Status | Condition | Detail |
|--------|-----------|--------|
| `400` | Not a CSV file | `"Only CSV files are accepted."` |
| `400` | Empty file | `"Uploaded file is empty."` |
| `400` | Cannot decode | `"Unable to decode file. Save the CSV as UTF-8 and try again."` |
| `400` | No headers | `"CSV file has no headers."` |
| `400` | Missing date column | `"CSV missing a date column..."` |
| `400` | Missing merchant column | `"CSV missing a merchant column..."` |
| `400` | Missing amount columns | `"CSV must have an 'amount' column, or separate 'debit' and 'credit' columns."` |
| `400` | No valid rows parsed | `"No valid transactions found in the file."` |

**Sample CSV (HDFC format)**
```csv
date,narration,amount
01/01/2025,SWIGGY ONLINE ORDER,350.00
02/01/2025,SALARY CREDIT MONTHLY,-50000.00
03/01/2025,ATM WDL HDFC,2000.00
```

---

### `GET /transactions`

List transactions for the authenticated user with pagination, search, and filtering.

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int ≥ 1 | `1` | Page number |
| `limit` | int 1–100 | `20` | Items per page |
| `search` | string | — | Case-insensitive search on merchant, description, category |
| `category` | string | — | Filter by exact category name |
| `month` | int 1–12 | — | Filter by month number |
| `year` | int | — | Filter by year |

**Response `200 OK`**

```json
{
  "transactions": [
    {
      "id": 101,
      "date": "2025-01-15",
      "merchant": "SWIGGY ONLINE ORDER",
      "description": null,
      "amount": 350.00,
      "transaction_type": "debit",
      "category": "Food",
      "source_file": "january_statement.csv",
      "predicted_category": "Food",
      "prediction_confidence": 0.982,
      "categorization_method": "ml",
      "created_at": "2025-06-01T10:30:00"
    }
  ],
  "total": 147,
  "page": 1,
  "limit": 20,
  "total_pages": 8
}
```

| Field | Description |
|-------|-------------|
| `transaction_type` | `"debit"` or `"credit"` |
| `category` | One of 15 categories: Food, Transport, Shopping, Entertainment, Health, Utilities, Income, Cash, Transfers, Insurance, Investment, Education, Rent, Subscriptions, Other |
| `predicted_category` | Same as `category` (ML's prediction, stored separately) |
| `prediction_confidence` | Float 0.0–1.0, `null` if rule engine was used |
| `categorization_method` | `"ml"` or `"rule_fallback"` |

**Transactions are ordered by:** `date DESC, id DESC`

---

### `GET /transactions/summary`

Aggregate statistics for the authenticated user's transactions, optionally filtered by month/year.

**Query Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `month` | int 1–12 | Filter to a specific month |
| `year` | int | Filter to a specific year |

**Response `200 OK`**

```json
{
  "total_transactions": 147,
  "total_spending": 32450.50,
  "total_income": 55000.00,
  "top_category": "Food",
  "largest_expense": 8500.00
}
```

| Field | Description |
|-------|-------------|
| `total_spending` | Sum of all debit transaction amounts |
| `total_income` | Sum of all credit transaction amounts |
| `top_category` | Category with highest total debit amount |
| `largest_expense` | Single largest debit amount |

---

### `GET /transactions/categories`

Return a sorted list of distinct category names present in the user's transactions.

**Response `200 OK`**

```json
["Cash", "Entertainment", "Food", "Health", "Income", "Shopping", "Transport", "Utilities"]
```

---

## 3. Analytics

All analytics endpoints require Bearer JWT. All calculations are performed over the user's **entire transaction history** (no date filter — use `/transactions/summary` for filtered period stats).

---

### `GET /analytics/overview`

Total income, expenses, net savings, and savings rate across all transactions.

**Response `200 OK`**

```json
{
  "income": 165000.00,
  "expense": 97450.50,
  "savings": 67549.50,
  "savings_rate": 40.9
}
```

| Field | Calculation |
|-------|------------|
| `income` | Sum of all `credit` transactions |
| `expense` | Sum of all `debit` transactions |
| `savings` | `income - expense` |
| `savings_rate` | `(savings / income) * 100`, rounded to 1 decimal |

---

### `GET /analytics/monthly-trend`

Monthly spending totals for the most recent 12 months.

**Response `200 OK`**

```json
{
  "data": [
    { "month": "Jul 24", "spending": 24500.00 },
    { "month": "Aug 24", "spending": 31200.00 },
    { "month": "Sep 24", "spending": 28750.00 },
    { "month": "Jun 25", "spending": 32450.50 }
  ]
}
```

Only debit transactions contribute to `spending`. Months with no transactions are omitted. Maximum 12 entries returned (last 12 months with data).

---

### `GET /analytics/category-breakdown`

Spending breakdown by category, sorted by amount descending, with percentage share.

**Response `200 OK`**

```json
{
  "data": [
    { "category": "Food", "amount": 18500.00, "percentage": 19.0, "count": 42 },
    { "category": "Shopping", "amount": 15200.00, "percentage": 15.6, "count": 18 },
    { "category": "Transport", "amount": 12000.00, "percentage": 12.3, "count": 35 }
  ]
}
```

| Field | Description |
|-------|-------------|
| `amount` | Total debit amount for this category |
| `percentage` | `(amount / total_expense) * 100` |
| `count` | Number of debit transactions in this category |

---

### `GET /analytics/top-merchants`

Top 5 merchants by total debit spend.

**Response `200 OK`**

```json
{
  "data": [
    { "merchant": "SWIGGY ONLINE ORDER", "total_amount": 8500.00, "transaction_count": 24 },
    { "merchant": "AMAZON ORDER ONLINE", "total_amount": 7200.00, "transaction_count": 12 },
    { "merchant": "UBER TRIP BOOKING", "total_amount": 4500.00, "transaction_count": 31 }
  ]
}
```

---

### `GET /analytics/cashflow`

Month-by-month income and expense, for the last 12 months with data. Suitable for rendering an area/bar comparison chart.

**Response `200 OK`**

```json
{
  "data": [
    { "month": "Jan 25", "income": 55000.00, "expense": 32000.00 },
    { "month": "Feb 25", "income": 55000.00, "expense": 28500.00 },
    { "month": "Mar 25", "income": 55000.00, "expense": 36800.00 }
  ]
}
```

---

### `GET /analytics/heatmap`

Average and total spending by day of week, for all debit transactions.

**Response `200 OK`**

```json
{
  "data": [
    { "day": "Mon", "average_spending": 850.00, "total_spending": 12750.00, "transaction_count": 15 },
    { "day": "Tue", "average_spending": 620.00, "total_spending": 9300.00, "transaction_count": 15 },
    { "day": "Sat", "average_spending": 1850.00, "total_spending": 22200.00, "transaction_count": 12 },
    { "day": "Sun", "average_spending": 2100.00, "total_spending": 16800.00, "transaction_count": 8 }
  ]
}
```

Days are always returned in order: Mon, Tue, Wed, Thu, Fri, Sat, Sun.

---

### `GET /analytics/health-score`

Composite financial health score (0–100) with grade, status, component breakdown, and personalized insights.

**Response `200 OK`**

```json
{
  "score": 74,
  "grade": "B",
  "status": "Good",
  "breakdown": {
    "savings_rate": 31.5,
    "savings_rate_max": 35,
    "expense_stability": 22.3,
    "expense_stability_max": 25,
    "income_consistency": 24.8,
    "income_consistency_max": 25,
    "diversification": 9.2,
    "diversification_max": 15
  },
  "insights": [
    "Savings rate of 27%. Aim for 20%+ for long-term security.",
    "Monthly expenses are consistent — a sign of disciplined spending.",
    "Income is highly consistent — strong financial foundation."
  ]
}
```

**Score Grading**

| Score | Grade | Status |
|-------|-------|--------|
| 90–100 | A+ | Excellent |
| 80–89 | A | Very Good |
| 70–79 | B | Good |
| 60–69 | C | Fair |
| 0–59 | D | Needs Improvement |

**Component Weights**

| Component | Max Score | Algorithm |
|-----------|-----------|-----------|
| Savings Rate | 35 pts | `min(35, savings_rate * 35/30)` — full score at 30%+ |
| Expense Stability | 25 pts | `25 * (1 - min(1, CV))` where CV = stdev/mean of monthly expense |
| Income Consistency | 25 pts | `25 * (1 - min(1, CV))` where CV = stdev/mean of monthly income |
| Category Diversification | 15 pts | `15 * (1 - HHI)` where HHI = Herfindahl-Hirschman Index of category shares |

---

## 4. Budgets

All budget endpoints require Bearer JWT.

---

### `GET /budgets`

List all budgets for the authenticated user, enriched with real-time current-month spending progress.

**Response `200 OK`**

```json
[
  {
    "id": 1,
    "category": "Food",
    "monthly_limit": 8000.00,
    "current_spend": 5200.00,
    "remaining": 2800.00,
    "pct_used": 65.0,
    "risk": "watch",
    "created_at": "2025-05-01T10:00:00"
  }
]
```

**Risk Level Logic**

| `pct_used` | `risk` |
|-----------|--------|
| < 60% | `"safe"` |
| 60%–84.9% | `"watch"` |
| 85%–99.9% | `"high"` |
| ≥ 100% | `"exceeded"` |

`current_spend` counts only **debit transactions in the current calendar month** matching the budget's category.

---

### `POST /budgets`

Create a new budget. Each category can have at most one budget per user.

**Request Body**

```json
{
  "category": "Food",
  "monthly_limit": 8000.00
}
```

| Field | Type | Constraints |
|-------|------|------------|
| `category` | string | Any string, typically from the 15 standard categories |
| `monthly_limit` | float | Must be > 0 |

**Response `201 Created`**

```json
{
  "id": 3,
  "category": "Food",
  "monthly_limit": 8000.00,
  "created_at": "2025-06-08T09:15:00",
  "updated_at": "2025-06-08T09:15:00"
}
```

**Error Responses**

| Status | Condition | Detail |
|--------|-----------|--------|
| `400` | `monthly_limit <= 0` | `"Monthly limit must be greater than 0."` |
| `400` | Category budget already exists | `"A budget for 'Food' already exists."` |

---

### `PUT /budgets/{budget_id}`

Update the monthly limit of an existing budget.

**Path Parameter:** `budget_id` (int)

**Request Body**

```json
{
  "monthly_limit": 10000.00
}
```

**Response `200 OK`**

```json
{
  "id": 3,
  "category": "Food",
  "monthly_limit": 10000.00,
  "created_at": "2025-06-08T09:15:00",
  "updated_at": "2025-06-08T10:30:00"
}
```

**Error Responses**

| Status | Condition | Detail |
|--------|-----------|--------|
| `400` | `monthly_limit <= 0` | `"Monthly limit must be greater than 0."` |
| `404` | Budget not found or not owned by user | `"Budget not found."` |

---

### `DELETE /budgets/{budget_id}`

Delete a budget.

**Response `204 No Content`** (empty body)

**Error Responses**

| Status | Condition |
|--------|-----------|
| `404` | Budget not found or not owned by user |

---

### `GET /budgets/overview`

Aggregate totals across all budgets for the authenticated user.

**Response `200 OK`**

```json
{
  "total_budget": 35000.00,
  "total_spent": 18750.50,
  "remaining": 16249.50,
  "at_risk_count": 2
}
```

| Field | Description |
|-------|-------------|
| `total_budget` | Sum of all `monthly_limit` values |
| `total_spent` | Sum of current-month spend across all budget categories |
| `remaining` | `total_budget - total_spent` |
| `at_risk_count` | Count of budgets with `risk` in `["high", "exceeded"]` |

Returns all zeros if no budgets exist.

---

### `GET /budgets/forecast`

End-of-month spending projection for all budgets, using the current month's daily spend rate.

**Response `200 OK`**

```json
{
  "forecasts": [
    {
      "category": "Food",
      "budget": 8000.00,
      "current_spend": 5200.00,
      "projected_spend": 10400.00,
      "expected_overrun": 2400.00,
      "risk": "exceeded",
      "daily_rate": 325.00,
      "days_remaining": 22
    }
  ],
  "alerts": [
    "Food budget likely to exceed by ₹2,400 this month"
  ],
  "month": 6,
  "year": 2025
}
```

**Forecast Algorithm**

```
daily_rate = current_spend / days_elapsed
projected_spend = daily_rate * days_in_month
expected_overrun = max(0, projected_spend - monthly_limit)
```

**Alert Generation Rules**

| Condition | Alert Message |
|-----------|--------------|
| `risk == "exceeded"` | `"{category} budget exceeded by ₹{overrun:,}"` |
| `risk == "high"` AND `overrun > 0` | `"{category} budget likely to exceed by ₹{overrun:,} this month"` |
| `risk == "watch"` AND `pct_now > 65%` | `"{category} is at {pct}% of budget — spending pace is elevated"` |

Returns empty `forecasts` and `alerts` if no budgets exist.

---

## 5. ML Model

This endpoint does **not** require authentication.

---

### `GET /ml/model-info`

Returns the status and metadata of the loaded ML categorization model.

**Response when model is loaded `200 OK`**

```json
{
  "status": "loaded",
  "algorithm": "XGBoost",
  "accuracy": 0.6910,
  "num_categories": 15,
  "categories": [
    "Cash", "Education", "Entertainment", "Food", "Health",
    "Income", "Insurance", "Investment", "Other", "Rent",
    "Shopping", "Subscriptions", "Transfers", "Transport", "Utilities"
  ],
  "num_training_samples": 711,
  "trained_at": "2025-06-07T14:23:11Z",
  "per_class_metrics": {
    "Food": { "precision": 0.792, "recall": 0.826, "f1_score": 0.809, "support": 23 },
    "Insurance": { "precision": 0.909, "recall": 0.909, "f1_score": 0.909, "support": 11 },
    "Cash": { "precision": 0.800, "recall": 1.000, "f1_score": 0.889, "support": 8 }
  }
}
```

**Response when model is not loaded `200 OK`**

```json
{
  "status": "not_loaded",
  "message": "No trained model found. Run scripts/train_transaction_classifier.py to train the model, then restart the server."
}
```

---

## 6. Error Reference

### Standard HTTP Error Format

FastAPI returns validation and application errors in this format:

```json
{
  "detail": "Error message here"
}
```

For Pydantic validation errors (`422`):

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required"
    }
  ]
}
```

### Authentication Errors

All protected endpoints return `401` with `WWW-Authenticate: Bearer` when:
- No `Authorization` header is present
- Token is expired, malformed, or uses wrong algorithm
- `user_id` claim is missing from token payload
- User referenced in token no longer exists in DB

```json
{
  "detail": "Invalid authentication token"
}
```

### CORS Policy

All origins are permitted (`allow_origins=["*"]`). This is configured for local development. In production, restrict to your actual frontend domain.

---

## Request Examples (cURL)

### Sign up
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Kawin Kumar","email":"kawin@example.com","password":"mypassword"}'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"kawin@example.com","password":"mypassword"}'
```

### Upload CSV
```bash
curl -X POST http://localhost:8000/transactions/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/statement.csv"
```

### Get transactions with filters
```bash
curl "http://localhost:8000/transactions?page=1&limit=20&category=Food&month=6&year=2025" \
  -H "Authorization: Bearer <token>"
```

### Get analytics overview
```bash
curl http://localhost:8000/analytics/overview \
  -H "Authorization: Bearer <token>"
```

### Get financial health score
```bash
curl http://localhost:8000/analytics/health-score \
  -H "Authorization: Bearer <token>"
```

### Create budget
```bash
curl -X POST http://localhost:8000/budgets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"category":"Food","monthly_limit":8000}'
```

### Check ML model status
```bash
curl http://localhost:8000/ml/model-info
```

---

## API Endpoint Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/signup` | — | Create user account |
| POST | `/auth/login` | — | Authenticate, get JWT |
| POST | `/transactions/upload` | JWT | Upload CSV statement |
| GET | `/transactions` | JWT | List transactions (paginated) |
| GET | `/transactions/summary` | JWT | Aggregate spending stats |
| GET | `/transactions/categories` | JWT | Distinct category list |
| GET | `/analytics/overview` | JWT | Income / expense / savings |
| GET | `/analytics/monthly-trend` | JWT | 12-month spending history |
| GET | `/analytics/category-breakdown` | JWT | Spend by category |
| GET | `/analytics/top-merchants` | JWT | Top 5 merchants by spend |
| GET | `/analytics/cashflow` | JWT | Monthly income vs expense |
| GET | `/analytics/heatmap` | JWT | Spend by day of week |
| GET | `/analytics/health-score` | JWT | Financial health score |
| GET | `/budgets` | JWT | List budgets with progress |
| POST | `/budgets` | JWT | Create budget |
| PUT | `/budgets/{id}` | JWT | Update budget limit |
| DELETE | `/budgets/{id}` | JWT | Delete budget |
| GET | `/budgets/overview` | JWT | Aggregate budget stats |
| GET | `/budgets/forecast` | JWT | End-of-month projection |
| GET | `/ml/model-info` | — | ML model status + metrics |
