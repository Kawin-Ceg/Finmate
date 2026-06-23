"""
Pytest fixtures for the FinMate backend test suite.

Tests run against a temporary file-based SQLite database (not the real
PostgreSQL instance configured in .env) and force GEMINI_API_KEY off so
Mate always uses its deterministic rule-based fallback instead of making
real network calls during tests.

IMPORTANT: the DATABASE_URL / GEMINI_API_KEY env vars below must be set
before any `app.*` module is imported, since app.database.database reads
DATABASE_URL at import time and binds the SQLAlchemy engine to it once.
"""
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

_tmp_db = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ["GEMINI_API_KEY"] = ""
os.environ.setdefault("SECRET_KEY", "test_only_secret_key_not_for_production")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database.database import Base, engine, SessionLocal
from app.models import (  # noqa: F401  (side-effect import registers all ORM models)
    User, Transaction, Budget, Anomaly, UserSettings, UserSession,
    ChatSession, ChatMessage,
)
from app.routes.auth import router as auth_router
from app.routes.transactions import router as transactions_router
from app.routes.analytics import router as analytics_router
from app.routes.budgets import router as budgets_router
from app.routes.anomalies import router as anomalies_router
from app.routes.mate import router as mate_router
from app.routes.dashboard import router as dashboard_router
from app.routes.settings_route import router as settings_router
from app.routes.security import router as security_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
for _router in (
    auth_router,
    transactions_router,
    analytics_router,
    budgets_router,
    anomalies_router,
    mate_router,
    dashboard_router,
    settings_router,
    security_router,
):
    app.include_router(_router)


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def new_user_creds():
    unique = uuid.uuid4().hex[:10]
    return {
        "name": "Test User",
        "email": f"test_{unique}@example.com",
        "password": "StrongPass123!",
    }


@pytest.fixture()
def auth_client(client, new_user_creds):
    """A (client, headers, user_creds) tuple for an already signed-up + logged-in user."""
    signup_resp = client.post("/auth/signup", json=new_user_creds)
    assert signup_resp.status_code == 200, signup_resp.text

    login_resp = client.post(
        "/auth/login",
        json={"email": new_user_creds["email"], "password": new_user_creds["password"]},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return client, headers, new_user_creds
