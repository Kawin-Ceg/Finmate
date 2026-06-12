# FinMate — Developer Guide

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Repository Structure](#2-repository-structure)
3. [Backend Setup](#3-backend-setup)
4. [Frontend Setup](#4-frontend-setup)
5. [Database Initialization](#5-database-initialization)
6. [Environment Variables](#6-environment-variables)
7. [Training the ML Model](#7-training-the-ml-model)
8. [Running the Full Stack](#8-running-the-full-stack)
9. [Development Workflow](#9-development-workflow)
10. [Authentication Implementation](#10-authentication-implementation)
11. [Adding a New API Endpoint](#11-adding-a-new-api-endpoint)
12. [Adding a New Frontend Page](#12-adding-a-new-frontend-page)
13. [Testing Manually](#13-testing-manually)
14. [Deployment Guide](#14-deployment-guide)
15. [Technical Interview Q&A](#15-technical-interview-qa)

---

## 1. Prerequisites

| Tool | Minimum Version | Install |
|------|----------------|---------|
| Python | 3.10+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| npm | 9+ | Included with Node.js |
| PostgreSQL | 14+ | [postgresql.org](https://postgresql.org) |
| Git | Any | [git-scm.com](https://git-scm.com) |

---

## 2. Repository Structure

```
finmate/
├── backend/          ← Python FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   ├── .env          ← (create this — not in git)
│   ├── models/       ← ML artifacts (generated — not in git)
│   ├── data/         ← Training data
│   ├── scripts/      ← Standalone CLI tools
│   └── app/          ← Application package
│       ├── models/   ← SQLAlchemy ORM
│       ├── schemas/  ← Pydantic I/O
│       ├── routes/   ← API endpoints
│       ├── services/ ← Business logic
│       ├── database/ ← DB engine + session
│       ├── utils/    ← Auth helpers
│       └── dependencies.py
└── frontend/         ← React Vite frontend
    ├── package.json
    ├── src/
    │   ├── App.jsx
    │   ├── context/
    │   ├── pages/
    │   ├── services/
    │   └── components/
    └── ...
```

---

## 3. Backend Setup

### 1. Create and activate a virtual environment

```bash
cd finmate/backend
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
```
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
pydantic>=2.0.0
python-dotenv>=1.0.0
python-multipart>=0.0.6
scikit-learn>=1.3.0
xgboost>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
```

### 3. Create the `.env` file

```bash
# finmate/backend/.env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/finmate
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
```

> Generate a secure SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`

### 4. Start the backend server

```bash
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`.

On first startup, you will see:
```
DATABASE_URL = postgresql://postgres:...
INFO     Tables created via create_all
INFO     ML classifier loaded: XGBoost | accuracy=69.10%
INFO     Application startup complete.
INFO     Uvicorn running on http://127.0.0.1:8000
```

**Auto-generated API docs:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 4. Frontend Setup

### 1. Install dependencies

```bash
cd finmate/frontend
npm install
```

### 2. Start the development server

```bash
npm run dev
```

Vite starts at `http://localhost:5173` with hot module replacement.

### 3. Build for production

```bash
npm run build
```

Output goes to `frontend/dist/`. Serve with any static file server.

### API Base URL

The frontend is hardcoded to connect to `http://localhost:8000` via `src/services/api.js`. For a different backend URL:

```javascript
// src/services/api.js
const api = axios.create({
  baseURL: 'https://your-backend.example.com',  // ← change this
});
```

---

## 5. Database Initialization

### Create the PostgreSQL database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE finmate;

# Exit
\q
```

### Tables are created automatically

On first `uvicorn main:app --reload`, SQLAlchemy runs:
```python
Base.metadata.create_all(bind=engine)
```

This creates the `users`, `transactions`, and `budgets` tables if they don't exist.

### Verify tables exist

```bash
psql -U postgres -d finmate

\dt
```

Expected output:
```
 Schema |     Name     | Type  |  Owner
--------+--------------+-------+----------
 public | budgets      | table | postgres
 public | transactions | table | postgres
 public | users        | table | postgres
```

### Reset the database (development)

```bash
psql -U postgres -d finmate
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
\q
```

Then restart the server to recreate tables.

---

## 6. Environment Variables

All environment variables are loaded from `backend/.env` via `python-dotenv`.

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql://postgres:pass@localhost:5432/finmate` | Full SQLAlchemy connection string |
| `SECRET_KEY` | Yes | `a3f8...` (32 hex chars) | JWT signing key |
| `ALGORITHM` | Yes | `HS256` | JWT algorithm |

**How variables are loaded:**

```python
# app/utils/auth.py and app/database/database.py
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)
SECRET_KEY = os.getenv("SECRET_KEY")
```

The path is computed relative to the file location, so it always finds `.env` in the `backend/` directory.

---

## 7. Training the ML Model

The ML model is **not included in the repository** (large binary files). You must train it once before categorization works.

### Train with the default dataset (889 samples)

```bash
cd finmate/backend
python scripts/train_transaction_classifier.py
```

Expected output:
```
INFO  Loaded 889 samples | 15 categories
INFO  Train: 711  |  Test: 178
INFO  Fitting TF-IDF vectorizer …
INFO  Training XGBoost (n_estimators=300) …
INFO  (classification report printed here)
INFO  Overall accuracy: 0.6910  (69.10%)
INFO  Model artifacts saved to: ...backend/models

==================================================
  Algorithm  : XGBoost
  Accuracy   : 69.10%
  Categories : 15
  Train size : 711
  Test size  : 178
==================================================

Model saved to: backend/models
Restart the backend server to load the new model.
```

### Train with a custom Kaggle dataset

```bash
# Download and prepare your CSV with columns: merchant_name, category
python scripts/train_transaction_classifier.py --dataset /path/to/kaggle_data.csv
```

### Verify model is loaded

After restarting the server, check:
```bash
curl http://localhost:8000/ml/model-info
```

Should return `"status": "loaded"`.

---

## 8. Running the Full Stack

### Terminal 1 — Backend

```bash
cd finmate/backend
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate      # macOS/Linux
uvicorn main:app --reload
```

### Terminal 2 — Frontend

```bash
cd finmate/frontend
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 9. Development Workflow

### Backend Code Organization

**Adding a new route**: Create or update a file in `app/routes/`. Register the router in `main.py`.

**Adding a new service**: Create a file in `app/services/`. Import and call it from the appropriate route.

**Modifying a database model**: Edit the model in `app/models/`. For adding columns, add an `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statement to `_ensure_ml_columns()` in `main.py`, or create a new migration function.

**Hot reload**: `uvicorn --reload` watches for file changes and restarts automatically.

### Frontend Code Organization

**Adding a new page**:
1. Create `src/pages/NewPage/NewPage.jsx`
2. Add a route in `src/App.jsx`
3. Add a sidebar link in `src/pages/Dashboard/components/Sidebar.jsx`

**Adding a new API call**: Add a function to the appropriate service file in `src/services/`.

**Shared components**: Place reusable UI components in `src/components/`.

---

## 10. Authentication Implementation

### Password Hashing

Uses `passlib` with bcrypt:

```python
# app/utils/auth.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### JWT Token Creation

```python
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

Token payload: `{"user_id": int, "email": str, "exp": datetime}`

### JWT Verification (Dependency)

```python
# app/dependencies.py
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

Any route that depends on `get_current_user` is automatically protected.

### Frontend Token Handling

```javascript
// context/AuthContext.jsx
const login = (userData, token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
};

// services/api.js — interceptor
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});
```

---

## 11. Adding a New API Endpoint

**Example:** Add `GET /transactions/{id}` to fetch a single transaction.

### Step 1: Add to `app/routes/transactions.py`

```python
@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return txn
```

No changes needed in `main.py` — the router is already registered.

### Step 2: Add to the frontend service

```javascript
// src/services/transactionService.js
export const getTransaction = async (id) => {
    const response = await api.get(`/transactions/${id}`);
    return response.data;
};
```

### Step 3: Use in a React component

```javascript
import { getTransaction } from '../../services/transactionService';

const [txn, setTxn] = useState(null);
useEffect(() => {
    getTransaction(transactionId).then(setTxn).catch(console.error);
}, [transactionId]);
```

---

## 12. Adding a New Frontend Page

**Example:** Add a `/dashboard/settings` page.

### Step 1: Create the page component

```
src/pages/Settings/Settings.jsx
src/pages/Settings/Settings.css
```

```jsx
// Settings.jsx
import Topbar from '../Dashboard/components/Topbar';

export default function Settings() {
    return (
        <>
            <Topbar title="Settings" />
            <div className="dashboard-content">
                <h1>Settings</h1>
            </div>
        </>
    );
}
```

### Step 2: Add route in `App.jsx`

```jsx
import Settings from './pages/Settings/Settings';

// Inside the /dashboard route:
<Route path="settings" element={<Settings />} />
```

### Step 3: Add sidebar link in `Sidebar.jsx`

```jsx
{ path: '/dashboard/settings', icon: <Settings size={16} />, label: 'Settings' }
```

---

## 13. Testing Manually

### Backend — using curl

```bash
# Health check
curl http://localhost:8000/

# Sign up
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Upload CSV
curl -X POST http://localhost:8000/transactions/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/statement.csv"

# Get transactions
curl "http://localhost:8000/transactions?page=1&limit=5" \
  -H "Authorization: Bearer $TOKEN"

# Health score
curl http://localhost:8000/analytics/health-score \
  -H "Authorization: Bearer $TOKEN"
```

### Backend — using Swagger UI

Open `http://localhost:8000/docs`. Click "Authorize" and enter your JWT token.

### Frontend — using browser DevTools

1. Open DevTools (F12) → Network tab
2. Perform actions in the UI
3. Inspect API requests and responses

---

## 14. Deployment Guide

### Backend Deployment (Ubuntu/Debian VPS)

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql nginx

# 2. Create database
sudo -u postgres createdb finmate
sudo -u postgres psql -c "CREATE USER finmate_user WITH PASSWORD 'securepass';"
sudo -u postgres psql -c "GRANT ALL ON DATABASE finmate TO finmate_user;"

# 3. Set up application
cd /var/www
git clone <your-repo> finmate
cd finmate/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure .env
cat > .env << EOF
DATABASE_URL=postgresql://finmate_user:securepass@localhost:5432/finmate
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ALGORITHM=HS256
EOF

# 5. Train ML model
python scripts/train_transaction_classifier.py

# 6. Create systemd service
sudo cat > /etc/systemd/system/finmate.service << EOF
[Unit]
Description=FinMate FastAPI Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/finmate/backend
ExecStart=/var/www/finmate/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable finmate
sudo systemctl start finmate
```

### Frontend Deployment (Nginx)

```bash
# 1. Build
cd /var/www/finmate/frontend

# Update API URL for production
sed -i "s|http://localhost:8000|https://api.yourdomain.com|g" src/services/api.js

npm install
npm run build

# 2. Nginx config
sudo cat > /etc/nginx/sites-available/finmate << EOF
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/finmate/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/finmate /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### ML Artifacts in Production

The `.pkl` model files are large (~4.3 MB total) and should not be in git. Options:
1. Train on the production server: `python scripts/train_transaction_classifier.py`
2. Upload the `backend/models/` directory via `scp` or object storage

```bash
# Option 2: Copy from local to server
scp -r backend/models/ user@yourserver:/var/www/finmate/backend/models/
```

### Environment Variable Management (Production)

Never commit `.env` to git. Use:
- **Systemd** `EnvironmentFile=` directive
- **Docker** `--env-file`
- **Cloud** (AWS Secrets Manager, Azure Key Vault, etc.)
- **Heroku** config vars

### CORS Configuration for Production

Change `allow_origins=["*"]` in `main.py` to your actual frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 15. Technical Interview Q&A

### FastAPI

**Q: Why FastAPI over Flask or Django?**  
A: FastAPI uses Python type hints + Pydantic for automatic request validation and generates OpenAPI docs at `/docs` without any additional code. Its async support via ASGI (Starlette) handles concurrent requests efficiently. Django is heavier and better suited for template-driven apps; Flask requires more boilerplate for validation and docs.

**Q: How does dependency injection work in FastAPI?**  
A: `Depends()` is a callable that FastAPI resolves before calling the route function. `get_db()` yields a session and closes it after the request. `get_current_user()` decodes the JWT and returns the user object. Dependencies can be chained — `get_current_user` itself depends on `get_db`.

**Q: What is the difference between `response_model` and the returned dict?**  
A: `response_model` is a Pydantic model that FastAPI uses to serialize and validate the outgoing response. If you return a SQLAlchemy ORM object, Pydantic's `from_attributes=True` config maps it to the schema. It also filters out fields not in the schema — a security feature that prevents leaking `password_hash`.

**Q: What is `python-multipart` for?**  
A: FastAPI requires it to handle `multipart/form-data` requests — specifically file uploads. Without it, `UploadFile` parsing fails.

---

### PostgreSQL

**Q: Why `psycopg2-binary` instead of `psycopg2`?**  
A: `psycopg2-binary` is a pre-compiled wheel that includes the C PostgreSQL client library statically, so no system-level `libpq-dev` installation is needed. For production, `psycopg2` (compiled from source) is preferred for security and performance, but `binary` is fine for development.

**Q: Why use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` instead of Alembic?**  
A: This project does not use Alembic migrations to keep the setup simple. For small schema additions (new nullable columns), the idempotent `IF NOT EXISTS` pattern is safe and runs on every startup. A production system with many developers should use Alembic for proper version-controlled migrations.

**Q: How does SQLAlchemy prevent SQL injection?**  
A: SQLAlchemy uses parameterized queries — ORM calls like `.filter(Transaction.user_id == user_id)` generate `WHERE user_id = $1` with the value bound separately. The `text()` function (used in `_ensure_ml_columns`) executes raw SQL, but with no user input — it's hardcoded DDL, not dynamic queries.

**Q: What is `server_default=func.now()`?**  
A: It sets the default value at the database level (SQL `DEFAULT NOW()`), not at the Python level. This means the database generates the timestamp, which is more accurate and consistent across multiple application instances.

---

### JWT Authentication

**Q: Why JWT over sessions?**  
A: JWTs are stateless — the server doesn't store session state. This makes horizontal scaling easier. The token carries the `user_id` claim, so the server only needs to verify the signature to trust the identity claim. The downside is revocation — a valid JWT cannot be invalidated without a server-side blocklist.

**Q: What's in the JWT payload?**  
A: `{"user_id": int, "email": str, "exp": datetime}`. The `exp` claim sets expiry to 24 hours from issue time.

**Q: Why store the token in `localStorage` vs `httpOnly` cookie?**  
A: `localStorage` is simpler for a JavaScript SPA. The tradeoff is XSS vulnerability — if an XSS attack runs on your page, it can read the token. `httpOnly` cookies are immune to XSS but vulnerable to CSRF. For a student/portfolio project, `localStorage` is an acceptable simplification.

**Q: How is the `HTTPBearer` scheme used?**  
A: FastAPI's `HTTPBearer` security scheme extracts the value from the `Authorization: Bearer <token>` header. It's not authentication itself — it just provides the raw token string that `get_current_user()` then decodes and verifies.

---

### React & Frontend

**Q: Why Context API instead of Redux?**  
A: FinMate has only two pieces of global state: `user` (auth) and `collapsed` (sidebar). Context API is sufficient — Redux adds significant boilerplate for state this simple. Redux is worthwhile when you have complex state interactions across many components.

**Q: What is the `AuthRoute` component?**  
A: It redirects already-authenticated users away from `/login` and `/signup` to `/dashboard`. Without it, a logged-in user could navigate to the login page by typing the URL directly.

**Q: How does the Axios interceptor work?**  
A: `api.interceptors.request.use(fn)` registers a function that runs before every request. The function reads the token from `localStorage` and adds `Authorization: Bearer <token>` to the request config. This means every `api.get()` / `api.post()` call is automatically authenticated without passing the token explicitly.

**Q: What is `useState(() => { ... })` (lazy initializer)?**  
A: Passing a function to `useState` instead of a value means the function only runs once (on mount), not on every render. Used in `AuthContext` and `SidebarContext` to read from `localStorage` only during initialization.

---

### CSV Processing

**Q: How does FinMate handle different bank CSV formats?**  
A: The `_find_column()` function normalizes column names (lowercase, replace spaces/dashes with underscores) and checks against a list of patterns. For example, `"Transaction Remarks"` normalizes to `"transaction_remarks"` and matches the pattern `"transaction"` in the merchant column patterns list.

**Q: How does it handle ambiguous amount formats?**  
A: `_parse_amount()` strips `₹`, `Rs.`, commas, and spaces. Parentheses like `(3500)` are treated as negative (debit) amounts — a common accounting format. If separate debit/credit columns exist, it checks which one is non-zero for each row.

**Q: How are 8 date formats handled?**  
A: `_parse_date()` iterates through `DATE_FORMATS` and tries `datetime.strptime()` for each. The first format that succeeds is used. Common formats include `%d/%m/%Y` (Indian standard), `%Y-%m-%d` (ISO), and `%d %b %Y` (e.g., "15 Jan 2025").

---

### Analytics & Health Score

**Q: How is the Herfindahl-Hirschman Index (HHI) used?**  
A: HHI = Σ(share²) where each share is a category's spending as a fraction of total spending. HHI = 1.0 means 100% concentration in one category; HHI approaches 0 with many equally-sized categories. Diversification score = `15 × (1 - HHI)`.

**Q: How is "expense stability" measured?**  
A: Coefficient of Variation (CV) = `stdev(monthly_expenses) / mean(monthly_expenses)`. A CV of 0 means perfectly stable; a CV of 1 means the standard deviation equals the mean (high volatility). Score = `25 × (1 - min(1, CV))`.

**Q: Why does the health score cap at 35 points for savings rate at 30%?**  
A: 30% savings rate is a widely recommended personal finance target (often cited by financial planners). The scoring formula `min(35, savings_rate × 35/30)` gives full marks at 30%+ and rewards any progress below that threshold proportionally.

---

### ML Categorization

**Q: Why TF-IDF instead of a simple bag-of-words?**  
A: TF-IDF down-weights common words ("payment", "transfer", "online") that appear across many categories and up-weights distinctive terms ("swiggy", "zerodha", "irctc") that are strong category signals. Sublinear TF scaling (`log(1+tf)`) prevents high-frequency words from dominating.

**Q: Why combine word and character n-grams?**  
A: Word n-grams capture full merchant names and two-word phrases (`"uber trip"`, `"apollo pharmacy"`). Character n-grams (3–5 chars) capture partial names (`"swig"`, `"netfl"`) and are robust to abbreviations and truncation common in bank statement narrations.

**Q: Why not use a neural network (BERT, etc.)?**  
A: XGBoost+TF-IDF is explainable, trains in seconds, produces probability scores natively, has no GPU requirement, and achieves good accuracy on this domain. The 889-sample dataset is also too small for effective fine-tuning of transformer models.

**Q: What would happen if you removed the confidence threshold?**  
A: Low-confidence ML predictions (e.g., 31% for "UBER TRIP") would be accepted. The model at 31% is essentially guessing — the rule engine with keyword "uber" → Transport is more reliable in this case.

**Q: Explain the gblinear vs gbtree choice.**  
A: `gblinear` fits linear models at each boosting step — faster but less expressive. `gbtree` (default) fits decision trees, which can model non-linear interactions. Testing showed `gblinear` achieved only 13% accuracy on this dataset (essentially predicting only the most common class), while `gbtree` achieved 69%. TF-IDF features are sparse and high-dimensional — tree-based boosting handles this well.

---

### Budget & Forecasting

**Q: How does the forecast algorithm work?**  
A: `daily_rate = current_month_spend / days_elapsed`. `projected_spend = daily_rate × days_in_month`. This is a linear projection assuming current spending pace continues for the rest of the month. It intentionally does not weight recent days more heavily — a simple, interpretable model.

**Q: What is the risk level for 84.9% usage?**  
A: `watch` (60%–84.9%). It becomes `high` at 85% and `exceeded` at 100%. These thresholds were chosen to give users 3 levels of warning before budget is fully consumed.
