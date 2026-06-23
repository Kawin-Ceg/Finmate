from app.models.anomaly import Anomaly
from app.models.user import User
from app.services.context_builder import build_context, context_to_prompt_text
from tests.helpers import recent_sample_csv, upload_sample_csv


def _get_user_id(db_session, email):
    return db_session.query(User).filter(User.email == email).first().id


def test_build_context_no_data(auth_client, db_session):
    _, _, creds = auth_client
    user_id = _get_user_id(db_session, creds["email"])
    ctx = build_context(user_id, db_session)
    assert ctx["has_data"] is False
    assert "no transaction data" in context_to_prompt_text(ctx).lower()


def test_build_context_with_data_has_correct_overview(auth_client, db_session):
    client, headers, creds = auth_client
    upload_sample_csv(client, headers, csv_text=recent_sample_csv())
    user_id = _get_user_id(db_session, creds["email"])

    ctx = build_context(user_id, db_session)
    assert ctx["has_data"] is True
    assert ctx["overview"]["income"] == 50000.0
    assert round(ctx["overview"]["expense"], 2) == 2329.50
    assert ctx["currency_symbol"] == "₹"  # default currency is INR


def test_top_merchant_amount_appears_correctly_in_prompt_text(auth_client, db_session):
    """
    Regression test for the bug where context_to_prompt_text looked up
    'total_spent'/'amount' keys that get_top_merchants never produces
    (it returns 'total_amount'), silently printing ₹0.00 for every merchant.
    """
    client, headers, creds = auth_client
    upload_sample_csv(client, headers, csv_text=recent_sample_csv())
    user_id = _get_user_id(db_session, creds["email"])

    ctx = build_context(user_id, db_session)
    assert ctx["top_merchants"], "expected at least one top merchant"
    biggest = max(ctx["top_merchants"], key=lambda m: m["total_amount"])
    assert biggest["total_amount"] > 0

    text = context_to_prompt_text(ctx)
    assert "TOP MERCHANTS" in text
    merchant_line = next(line for line in text.splitlines() if biggest["merchant"] in line)
    # the real amount must be printed, not a silent ₹0.00 fallback
    assert f"{biggest['total_amount']:,.2f}" in merchant_line


def test_subscription_anomaly_appears_in_context(auth_client, db_session):
    """
    Regression test for the bug where build_context() filtered anomalies by
    type == 'subscription_detected', but anomaly_service.py actually persists
    them as type == 'subscription', so ctx['subscriptions'] was always empty.
    """
    client, headers, creds = auth_client
    user_id = _get_user_id(db_session, creds["email"])

    anomaly = Anomaly(
        user_id=user_id,
        type="subscription",
        severity="low",
        title="Subscription: NETFLIX SUBSCRIPTION",
        description="Recurring charge detected.",
        score=20.0,
        meta_data={"avg_amount": 499.0},
    )
    db_session.add(anomaly)
    db_session.commit()

    ctx = build_context(user_id, db_session)
    assert len(ctx["subscriptions"]) == 1
    assert ctx["subscriptions"][0]["merchant"] == "NETFLIX SUBSCRIPTION"
    assert ctx["subscriptions"][0]["amount"] == 499.0


def test_mate_chat_endpoint_smoke(auth_client):
    client, headers, _ = auth_client
    resp = client.post("/mate/chat", headers=headers, json={"message": "How am I doing financially?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert body["session_id"]
    assert body["intent"] == "financial_summary"


def test_mate_suggestions_endpoint(auth_client):
    client, headers, _ = auth_client
    resp = client.get("/mate/suggestions", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 0
