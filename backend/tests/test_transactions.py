from tests.helpers import SAMPLE_CSV, upload_sample_csv


def test_upload_imports_all_valid_rows(auth_client):
    client, headers, _ = auth_client
    resp = upload_sample_csv(client, headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["transactions_imported"] == 5
    assert body["duplicates_skipped"] == 0


def test_upload_rejects_non_csv_file(auth_client):
    client, headers, _ = auth_client
    resp = client.post(
        "/transactions/upload",
        headers=headers,
        files={"file": ("statement.txt", "not a csv", "text/plain")},
    )
    assert resp.status_code == 400


def test_duplicate_upload_is_skipped(auth_client):
    client, headers, _ = auth_client
    first = upload_sample_csv(client, headers)
    assert first.json()["transactions_imported"] == 5

    second = upload_sample_csv(client, headers)
    body = second.json()
    assert body["transactions_imported"] == 0
    assert body["duplicates_skipped"] == 5
    assert second.status_code == 200


def test_partial_duplicate_upload_only_imports_new_rows(auth_client):
    client, headers, _ = auth_client
    upload_sample_csv(client, headers)

    extra_csv = SAMPLE_CSV + "20/01/2025,STARBUCKS COFFEE,-250.00\n"
    resp = upload_sample_csv(client, headers, csv_text=extra_csv, filename="statement2.csv")
    body = resp.json()
    assert body["transactions_imported"] == 1
    assert body["duplicates_skipped"] == 5


def test_uploaded_transactions_appear_in_list(auth_client):
    client, headers, _ = auth_client
    upload_sample_csv(client, headers)
    resp = client.get("/transactions", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5


def test_summary_reflects_income_and_spending(auth_client):
    client, headers, _ = auth_client
    upload_sample_csv(client, headers)
    resp = client.get("/transactions/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_income"] == 50000.00
    assert round(body["total_spending"], 2) == 2329.50
