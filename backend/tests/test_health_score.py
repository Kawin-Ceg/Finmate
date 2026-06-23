from datetime import date

from app.services.health_score_service import compute_health_score
from tests.helpers import upload_sample_csv


class _Txn:
    def __init__(self, amount, transaction_type, category, day):
        self.amount = amount
        self.transaction_type = transaction_type
        self.category = category
        self.date = day


def test_compute_health_score_no_transactions_returns_zero():
    result = compute_health_score([])
    assert result["score"] == 0
    assert result["grade"] == "D"


def test_compute_health_score_high_savings_rate_scores_well():
    txns = [
        _Txn(100000, "credit", "Income", date(2025, 1, 5)),
        _Txn(100000, "credit", "Income", date(2025, 2, 5)),
        _Txn(20000, "debit", "Food", date(2025, 1, 10)),
        _Txn(20000, "debit", "Food", date(2025, 2, 10)),
    ]
    result = compute_health_score(txns)
    # 80% savings rate should max out the savings-rate component (35 pts)
    assert result["breakdown"]["savings_rate"] == 35.0
    assert result["score"] >= 50


def test_compute_health_score_low_savings_rate_scores_poorly():
    txns = [
        _Txn(20000, "credit", "Income", date(2025, 1, 5)),
        _Txn(19000, "debit", "Food", date(2025, 1, 10)),
    ]
    result = compute_health_score(txns)
    assert result["breakdown"]["savings_rate"] < 10.0


def test_health_score_endpoint_returns_expected_shape(auth_client):
    client, headers, _ = auth_client
    upload_sample_csv(client, headers)
    resp = client.get("/analytics/health-score", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "score" in body and "grade" in body and "breakdown" in body
    assert 0 <= body["score"] <= 100


def test_health_score_endpoint_with_no_data(auth_client):
    client, headers, _ = auth_client
    resp = client.get("/analytics/health-score", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["score"] == 0
