# FinMate — Deployment Checklist

Use this before every production deploy.

## 1. Environment Variables

- [ ] `backend/.env` exists on the server and is **not** committed to git (already covered by `.gitignore`)
- [ ] `SECRET_KEY` — strong random value (`python -c "import secrets; print(secrets.token_hex(32))"`), different per environment
- [ ] `DATABASE_URL` — points at the production PostgreSQL instance, not localhost
- [ ] `ALGORITHM=HS256`
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` — set deliberately (shorter than 1440 for production is recommended, e.g. 60–240)
- [ ] `ENVIRONMENT=production`
- [ ] `CORS_ORIGINS` — set to the exact production frontend origin(s), comma-separated, no trailing slashes, no wildcard. **The app refuses all cross-origin requests if this is blank in production — by design, not a bug.**
- [ ] `GEMINI_API_KEY` — valid key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey). If blank, Mate falls back to a rule-based response (degraded but functional).
- [ ] `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `FROM_EMAIL` — set for real email delivery. If blank, OTPs are only logged to the server console (acceptable for staging, **not** for production — users would never receive their verification code).

## 2. Database

- [ ] PostgreSQL reachable from the app server
- [ ] First boot runs `Base.metadata.create_all()` + the `_ensure_*_columns()` idempotent migrations in `main.py` automatically — confirm the deploy logs show no `"Could not add ... columns"` warnings
- [ ] Take a backup/snapshot before every deploy that changes schema
- [ ] No automated migration tool (Alembic) is in place — schema evolution currently relies on hand-written `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements in `main.py`. Acceptable for the current scale; revisit if the schema starts changing frequently or destructively (column drops/renames aren't handled by this mechanism at all).

## 3. Uploads / Static Files

- [ ] `backend/static/avatars/` directory is writable by the app process
- [ ] If running multiple backend instances behind a load balancer, avatar uploads need shared storage (e.g. S3/Blob) — local disk storage does not survive across instances or redeploys

## 4. ML Model Artifacts

- [ ] `backend/models/transaction_model.pkl`, `vectorizer.pkl`, `label_encoder.pkl`, `training_report.json` are present on the server (they are gitignored — must be deployed separately or regenerated via `scripts/train_transaction_classifier.py`)
- [ ] If absent, the app still boots and falls back to rule-based categorization (`categorizer.py`) — confirmed by `load_model()` logging a warning rather than raising

## 5. Frontend Build

- [ ] `npm run build` in `frontend/` produces `dist/`
- [ ] `frontend/src/services/api.js` `baseURL` points at the production backend URL, not `localhost:8000`
- [ ] Static frontend is served over HTTPS (TLS termination is a hosting/reverse-proxy concern, not handled by the app itself)

## 6. Security Sign-off

- [ ] `.env.example` contains no real secrets (verified — placeholders only)
- [ ] `SECRET_KEY` rotated from any previously-used development value
- [ ] Gemini API key rotated if it was ever exposed in a committed file (see Production Readiness Report — this was found and fixed during this hardening pass; the key itself should still be rotated by the user at aistudio.google.com/apikey since it lived unredacted in `.env.example` for some period)
- [ ] CORS origins reviewed — no wildcards in production
- [ ] Login endpoint has no brute-force protection beyond normal password hashing cost (bcrypt). OTP verification has lockout; **plain login does not**. Consider rate-limiting `/auth/login` (e.g. via reverse proxy or a Redis-backed limiter) before high-stakes production launch.

## 7. Tests

- [ ] `cd backend && venv/Scripts/python.exe -m pytest tests/ -v` passes (41/41 at time of writing)
- [ ] Re-run after any change to auth, transactions, budgets, analytics, or Mate

## 8. Post-Deploy Smoke Test

- [ ] Sign up a test account, verify OTP arrives (email or console depending on SMTP config)
- [ ] Upload a sample CSV, confirm transactions + categorization appear
- [ ] Load `/dashboard/overview` and confirm all sections render (health score, budgets, anomalies, trends)
- [ ] Ask Mate a question, confirm a response comes back (LLM-backed or rule-based fallback)
- [ ] Log in from a second browser, revoke the first session from Settings → Security, confirm the first session is immediately rejected
