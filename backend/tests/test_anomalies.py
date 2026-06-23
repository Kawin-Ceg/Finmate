from tests.helpers import upload_sample_csv

# Recurring monthly charge at a consistent amount across 3 distinct months,
# which detect_subscriptions() should flag as type="subscription".
SUBSCRIPTION_CSV = """date,merchant,amount
05/01/2025,NETFLIX SUBSCRIPTION,-499.00
05/02/2025,NETFLIX SUBSCRIPTION,-499.00
05/03/2025,NETFLIX SUBSCRIPTION,-499.00
10/01/2025,SALARY CREDIT MONTHLY,50000.00
10/02/2025,SALARY CREDIT MONTHLY,50000.00
10/03/2025,SALARY CREDIT MONTHLY,50000.00
"""


def test_upload_triggers_anomaly_detection(auth_client):
    client, headers, _ = auth_client
    upload_sample_csv(client, headers, csv_text=SUBSCRIPTION_CSV)
    resp = client.get("/anomalies", headers=headers)
    assert resp.status_code == 200
    anomalies = resp.json()
    assert any(a["type"] == "subscription" for a in anomalies)


def test_manual_anomaly_run_is_idempotent(auth_client):
    client, headers, _ = auth_client
    upload_sample_csv(client, headers, csv_text=SUBSCRIPTION_CSV)
    first_count = len(client.get("/anomalies", headers=headers).json())

    rerun = client.post("/anomalies/run", headers=headers)
    assert rerun.status_code == 200
    second_count = len(client.get("/anomalies", headers=headers).json())
    # re-running detection wipes and recomputes — should be stable, not cumulative
    assert second_count == first_count


def test_subscriptions_endpoint_lists_detected_subscription(auth_client):
    client, headers, _ = auth_client
    upload_sample_csv(client, headers, csv_text=SUBSCRIPTION_CSV)
    resp = client.get("/anomalies/subscriptions", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    assert any(s["merchant"] == "NETFLIX SUBSCRIPTION" for s in body["subscriptions"])


def test_anomaly_summary_counts_by_severity(auth_client):
    client, headers, _ = auth_client
    upload_sample_csv(client, headers, csv_text=SUBSCRIPTION_CSV)
    resp = client.get("/anomalies/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == body["critical"] + body["high"] + body["medium"] + body["low"]


def test_no_anomalies_for_fresh_user(auth_client):
    client, headers, _ = auth_client
    resp = client.get("/anomalies", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []
