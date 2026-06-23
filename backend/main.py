import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.models import User, Transaction, Budget, Anomaly, UserSettings, UserSession, ChatSession, ChatMessage  # noqa: F401
from app.database.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.test import router as test_router
from app.routes.transactions import router as transactions_router
from app.routes.analytics import router as analytics_router
from app.routes.budgets import router as budgets_router
from app.routes.ml import router as ml_router
from app.routes.anomalies import router as anomalies_router
from app.routes.profile import router as profile_router
from app.routes.settings_route import router as settings_router
from app.routes.security import router as security_router
from app.routes.account import router as account_router
from app.routes.mate import router as mate_router
from app.routes.dashboard import router as dashboard_router
from app.services.ml_categorizer import load_model

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
_cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()

if _cors_origins_env:
    CORS_ORIGINS = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
elif ENVIRONMENT == "production":
    CORS_ORIGINS = []
    logger.warning("ENVIRONMENT=production but CORS_ORIGINS is not set — all cross-origin requests will be blocked.")
else:
    CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "avatars").mkdir(exist_ok=True)


def _ensure_ml_columns():
    stmts = [
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS predicted_category VARCHAR(100)",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS prediction_confidence FLOAT",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS categorization_method VARCHAR(20)",
    ]
    try:
        with engine.connect() as conn:
            for stmt in stmts:
                conn.execute(text(stmt))
            conn.commit()
    except Exception as exc:
        logger.warning("Could not add ML columns: %s", exc)


def _ensure_chat_columns():
    stmts = [
        "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS session_summary TEXT",
    ]
    try:
        with engine.connect() as conn:
            for stmt in stmts:
                conn.execute(text(stmt))
            conn.commit()
    except Exception as exc:
        logger.warning("Could not add chat columns: %s", exc)


def _ensure_user_columns():
    stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS country VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_code VARCHAR(10)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expiry TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_sent_at TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_failed_attempts INTEGER DEFAULT 0 NOT NULL",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_locked_until TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_timestamp TIMESTAMP",
    ]
    try:
        with engine.connect() as conn:
            for stmt in stmts:
                conn.execute(text(stmt))
            conn.commit()
    except Exception as exc:
        logger.warning("Could not add user columns: %s", exc)


Base.metadata.create_all(bind=engine)
_ensure_ml_columns()
_ensure_user_columns()
_ensure_chat_columns()
load_model()

app = FastAPI(title="FinMate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(test_router)
app.include_router(auth_router)
app.include_router(transactions_router)
app.include_router(analytics_router)
app.include_router(budgets_router)
app.include_router(ml_router)
app.include_router(anomalies_router)
app.include_router(profile_router)
app.include_router(settings_router)
app.include_router(security_router)
app.include_router(account_router)
app.include_router(mate_router)
app.include_router(dashboard_router)


@app.get("/")
def root():
    return {"message": "FinMate API Running"}
