from app.models.user import User
from app.models.user_session import UserSession


def test_signup_creates_unverified_user(client, new_user_creds):
    resp = client.post("/auth/signup", json=new_user_creds)
    assert resp.status_code == 200
    assert "verify" in resp.json()["message"].lower()


def test_signup_rejects_duplicate_email(client, new_user_creds):
    client.post("/auth/signup", json=new_user_creds)
    resp = client.post("/auth/signup", json=new_user_creds)
    assert resp.status_code == 400


def test_login_succeeds_with_correct_password(client, new_user_creds):
    client.post("/auth/signup", json=new_user_creds)
    resp = client.post(
        "/auth/login",
        json={"email": new_user_creds["email"], "password": new_user_creds["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["user"]["email"] == new_user_creds["email"]


def test_login_rejects_wrong_password(client, new_user_creds):
    client.post("/auth/signup", json=new_user_creds)
    resp = client.post(
        "/auth/login",
        json={"email": new_user_creds["email"], "password": "WrongPassword!"},
    )
    assert resp.status_code == 401


def test_login_creates_session_row(auth_client, db_session, new_user_creds):
    _, headers, creds = auth_client
    user = db_session.query(User).filter(User.email == creds["email"]).first()
    sessions = db_session.query(UserSession).filter(UserSession.user_id == user.id).all()
    assert len(sessions) == 1
    assert sessions[0].is_active is True


def test_protected_endpoint_requires_token(client):
    resp = client.get("/profile" if False else "/budgets")
    assert resp.status_code in (401, 403)


def test_protected_endpoint_works_with_valid_token(auth_client):
    client, headers, _ = auth_client
    resp = client.get("/budgets", headers=headers)
    assert resp.status_code == 200


def test_otp_verification_with_wrong_code_decrements_attempts(auth_client, db_session, new_user_creds):
    client, headers, creds = auth_client
    resp = client.post("/auth/verify-email", headers=headers, json={"otp": "000000"})
    assert resp.status_code == 400
    user = db_session.query(User).filter(User.email == creds["email"]).first()
    assert user.otp_failed_attempts == 1


def test_otp_lockout_after_five_failed_attempts(auth_client):
    client, headers, _ = auth_client
    for _ in range(5):
        resp = client.post("/auth/verify-email", headers=headers, json={"otp": "000000"})
    # 5th failure should trigger the lockout response
    assert resp.status_code == 429
    # A 6th attempt while locked must also be rejected with 429, regardless of OTP value
    resp2 = client.post("/auth/verify-email", headers=headers, json={"otp": "111111"})
    assert resp2.status_code == 429


def test_otp_verification_succeeds_with_correct_code(auth_client, db_session, new_user_creds):
    client, headers, creds = auth_client
    user = db_session.query(User).filter(User.email == creds["email"]).first()
    correct_otp = user.otp_code
    resp = client.post("/auth/verify-email", headers=headers, json={"otp": correct_otp})
    assert resp.status_code == 200
    db_session.refresh(user)
    assert user.email_verified is True
    assert user.otp_failed_attempts == 0


def test_session_revocation_blocks_further_requests(client, new_user_creds):
    client.post("/auth/signup", json=new_user_creds)

    login1 = client.post(
        "/auth/login",
        json={"email": new_user_creds["email"], "password": new_user_creds["password"]},
    )
    token1 = login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    login2 = client.post(
        "/auth/login",
        json={"email": new_user_creds["email"], "password": new_user_creds["password"]},
    )
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # both tokens work right after login
    assert client.get("/budgets", headers=headers1).status_code == 200
    assert client.get("/budgets", headers=headers2).status_code == 200

    # revoke session 1 using session 2's credentials
    sessions = client.get("/security/sessions", headers=headers2).json()
    target = next(s for s in sessions if not s["is_current"])
    revoke_resp = client.delete(f"/security/sessions/{target['id']}", headers=headers2)
    assert revoke_resp.status_code == 200

    # token1's session is now revoked -> must be rejected immediately, no waiting for JWT expiry
    assert client.get("/budgets", headers=headers1).status_code == 401
    # token2 still works
    assert client.get("/budgets", headers=headers2).status_code == 200
