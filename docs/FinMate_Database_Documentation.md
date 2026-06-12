# FinMate — Database Documentation

## Overview

FinMate uses **PostgreSQL** as its primary data store. The ORM layer is **SQLAlchemy 2.0** with `declarative_base`. Tables are created automatically on server startup via `Base.metadata.create_all(bind=engine)`. There is no Alembic migration framework — schema changes are applied via idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements.

---

## Connection Configuration

### Environment Variables (`.env`)

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/finmate
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
```

### SQLAlchemy Setup (`app/database/database.py`)

```python
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
```

### Session Dependency (`app/database/dependencies.py`)

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Each request gets a fresh database session via FastAPI's `Depends(get_db)`. The session is always closed after the request completes, whether or not an exception occurred.

---

## Entity-Relationship Diagram

```mermaid
erDiagram
    USERS {
        int id PK "AUTO_INCREMENT"
        varchar(100) name "NOT NULL"
        varchar(255) email "UNIQUE, NOT NULL"
        varchar password_hash "NOT NULL"
        datetime created_at "DEFAULT NOW()"
        datetime updated_at "DEFAULT NOW()"
    }

    TRANSACTIONS {
        int id PK "AUTO_INCREMENT"
        int user_id FK "NOT NULL, INDEX"
        date date "NOT NULL"
        varchar(255) merchant "NOT NULL"
        text description "NULLABLE"
        float amount "NOT NULL"
        varchar(10) transaction_type "NOT NULL, DEFAULT 'debit'"
        varchar(100) category "NOT NULL, DEFAULT 'Other'"
        varchar(255) source_file "NULLABLE"
        varchar(100) predicted_category "NULLABLE"
        float prediction_confidence "NULLABLE"
        varchar(20) categorization_method "NULLABLE"
        datetime created_at "DEFAULT NOW()"
        datetime updated_at "DEFAULT NOW(), ON UPDATE NOW()"
    }

    BUDGETS {
        int id PK "AUTO_INCREMENT"
        int user_id FK "NOT NULL, INDEX"
        varchar(100) category "NOT NULL"
        float monthly_limit "NOT NULL"
        datetime created_at "DEFAULT NOW()"
        datetime updated_at "DEFAULT NOW(), ON UPDATE NOW()"
    }

    USERS ||--o{ TRANSACTIONS : "cascade delete"
    USERS ||--o{ BUDGETS : "cascade delete"
```

---

## Table: `users`

**File:** `app/models/user.py`

Stores user account information. Passwords are stored as bcrypt hashes — never in plain text.

### Columns

| Column | Type | Nullable | Default | Constraints | Description |
|--------|------|----------|---------|-------------|-------------|
| `id` | Integer | No | Auto | PRIMARY KEY, INDEX | Unique user identifier |
| `name` | String(100) | No | — | — | Display name |
| `email` | String(255) | No | — | UNIQUE | Login email address |
| `password_hash` | String | No | — | — | bcrypt hash of password |
| `created_at` | DateTime | Yes | `func.now()` | — | Account creation timestamp |
| `updated_at` | DateTime | Yes | `func.now()` | — | Last update timestamp |

### Relationships

| Relationship | Target | Type | Cascade |
|-------------|--------|------|---------|
| `transactions` | `Transaction` | One-to-Many | `all, delete-orphan` |
| `budgets` | `Budget` | One-to-Many | `all, delete-orphan` |

When a user is deleted, all their transactions and budgets are automatically deleted.

### Indexes

- `id` — Primary Key (btree, unique)
- `email` — Unique index (btree), used for login query

### Sample Data

```sql
SELECT id, name, email, created_at FROM users LIMIT 3;

 id |     name      |          email          |        created_at
----+---------------+-------------------------+---------------------------
  1 | Kawin Kumar   | kawin@example.com       | 2025-06-01 09:00:00
  2 | Priya Sharma  | priya@example.com       | 2025-06-02 14:30:00
```

---

## Table: `transactions`

**File:** `app/models/transaction.py`

Stores all financial transactions imported from CSV statements. Contains both original transaction data and ML categorization metadata.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `user_id` | Integer (FK→users.id) | No | — | Owner user |
| `date` | Date | No | — | Transaction date |
| `merchant` | String(255) | No | — | Merchant / payee name (from CSV) |
| `description` | Text | Yes | — | Additional description (optional CSV column) |
| `amount` | Float | No | — | Absolute transaction amount (always positive) |
| `transaction_type` | String(10) | No | `'debit'` | `'debit'` or `'credit'` |
| `category` | String(100) | No | `'Other'` | Assigned category (from ML or rule engine) |
| `source_file` | String(255) | Yes | — | Original CSV filename |
| `predicted_category` | String(100) | Yes | — | ML model's category prediction (may equal `category`) |
| `prediction_confidence` | Float | Yes | — | ML confidence score (0.0–1.0), `NULL` if rule engine used |
| `categorization_method` | String(20) | Yes | — | `'ml'` or `'rule_fallback'` |
| `created_at` | DateTime | Yes | `func.now()` | Import timestamp |
| `updated_at` | DateTime | Yes | `func.now()` | Last update (auto-updates on change) |

### ML Column Notes

The three ML columns (`predicted_category`, `prediction_confidence`, `categorization_method`) were added after initial schema creation. They are applied idempotently at every server startup:

```python
# main.py
def _ensure_ml_columns():
    stmts = [
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS predicted_category VARCHAR(100)",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS prediction_confidence FLOAT",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS categorization_method VARCHAR(20)",
    ]
```

Transactions imported before the ML engine was added have `NULL` in all three columns.

### Transaction Type Semantics

| `transaction_type` | `amount` | Meaning |
|-------------------|---------|---------|
| `'debit'` | Positive float | Money leaving the account |
| `'credit'` | Positive float | Money entering the account |

Amount is always stored as a positive number. The sign is conveyed by `transaction_type`.

### Relationships

| Relationship | Target | Type | Back-reference |
|-------------|--------|------|---------------|
| `user` | `User` | Many-to-One | `User.transactions` |

### Indexes

- `id` — Primary Key
- `user_id` — Regular index (btree), used in all user-scoped queries

### Common Queries

**Get current month spending for a category:**
```sql
SELECT SUM(amount)
FROM transactions
WHERE user_id = 1
  AND category = 'Food'
  AND transaction_type = 'debit'
  AND EXTRACT(YEAR FROM date) = 2025
  AND EXTRACT(MONTH FROM date) = 6;
```

**Monthly spending trend:**
```sql
SELECT TO_CHAR(date, 'YYYY-MM') as month, SUM(amount) as spending
FROM transactions
WHERE user_id = 1
  AND transaction_type = 'debit'
GROUP BY month
ORDER BY month DESC
LIMIT 12;
```

---

## Table: `budgets`

**File:** `app/models/budget.py`

Stores monthly spending limits set by users per category. Budget tracking is always computed at query time against current-month transactions — no spend is stored in this table.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `user_id` | Integer (FK→users.id) | No | — | Owner user |
| `category` | String(100) | No | — | Spending category name |
| `monthly_limit` | Float | No | — | Monthly spending cap (must be > 0) |
| `created_at` | DateTime | Yes | `func.now()` | Creation timestamp |
| `updated_at` | DateTime | Yes | `func.now()` | Last update |

### Business Rules

- One budget per (user, category) pair — enforced by application logic (not a DB constraint)
- `monthly_limit` must be greater than 0 (enforced at the API layer)
- Deleting a user cascades to delete all their budgets

### Relationships

| Relationship | Target | Type |
|-------------|--------|------|
| `user` | `User` | Many-to-One |

### Indexes

- `id` — Primary Key
- `user_id` — Regular index

---

## Schema Migration Strategy

FinMate does not use Alembic. Schema changes are managed through two mechanisms:

### 1. Auto-create on startup

```python
Base.metadata.create_all(bind=engine)
```

This creates all tables if they don't exist (no-op if they do). It does **not** modify existing tables.

### 2. Idempotent ALTER TABLE for additions

For adding new columns to existing tables:

```python
def _ensure_ml_columns():
    stmts = [
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS predicted_category VARCHAR(100)",
        ...
    ]
    with engine.connect() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))
        conn.commit()
```

`IF NOT EXISTS` makes these statements safe to re-run on every startup.

### Manual Migration Script

For applying column additions without restarting the server:

```bash
cd backend
python scripts/migrate_add_ml_columns.py
```

---

## Data Integrity Notes

### User Scoping

Every query in the application filters by `user_id = current_user.id`. There is no risk of cross-user data leakage at the database level because:
1. The JWT dependency resolves `current_user` before any query executes
2. Every SQLAlchemy query adds `.filter(Model.user_id == current_user.id)`

### Cascade Delete Behavior

Deleting a user (via direct SQL — no API endpoint exists for this) will cascade-delete:
- All their transactions
- All their budgets

This is configured in the SQLAlchemy relationship:
```python
transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
```

### Amount Storage

All amounts are stored as `FLOAT` (double precision). For a production finance application this would ideally be `NUMERIC(15,2)` to avoid floating-point rounding. This is a known simplification appropriate for the current scope.

### No Soft Deletes

Transactions and budgets are hard-deleted. There is no `deleted_at` column or soft-delete pattern.

---

## Database Initialization (Fresh Setup)

```sql
-- Create the database
CREATE DATABASE finmate;

-- Connect to it
\c finmate

-- Tables are created automatically by FastAPI on first startup
-- No manual SQL needed
```

Then start the server:
```bash
uvicorn main:app --reload
```

On startup you will see:
```
INFO     Finished executing table creation
INFO     ML classifier loaded: XGBoost | accuracy=69.10%
INFO     Application startup complete.
```
