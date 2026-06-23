def test_create_budget_succeeds(auth_client):
    client, headers, _ = auth_client
    resp = client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": 5000})
    assert resp.status_code == 201
    body = resp.json()
    assert body["category"] == "Food"
    assert body["monthly_limit"] == 5000


def test_create_budget_rejects_zero_limit(auth_client):
    client, headers, _ = auth_client
    resp = client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": 0})
    assert resp.status_code == 422  # Pydantic Field(gt=0) validation


def test_create_budget_rejects_negative_limit(auth_client):
    client, headers, _ = auth_client
    resp = client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": -100})
    assert resp.status_code == 422


def test_create_budget_rejects_duplicate_category(auth_client):
    client, headers, _ = auth_client
    client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": 5000})
    resp = client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": 3000})
    assert resp.status_code == 400


def test_update_budget_succeeds(auth_client):
    client, headers, _ = auth_client
    create_resp = client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": 5000})
    budget_id = create_resp.json()["id"]
    update_resp = client.put(f"/budgets/{budget_id}", headers=headers, json={"monthly_limit": 7000})
    assert update_resp.status_code == 200
    assert update_resp.json()["monthly_limit"] == 7000


def test_update_budget_rejects_invalid_limit(auth_client):
    client, headers, _ = auth_client
    create_resp = client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": 5000})
    budget_id = create_resp.json()["id"]
    resp = client.put(f"/budgets/{budget_id}", headers=headers, json={"monthly_limit": 0})
    assert resp.status_code == 422


def test_delete_budget(auth_client):
    client, headers, _ = auth_client
    create_resp = client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": 5000})
    budget_id = create_resp.json()["id"]
    resp = client.delete(f"/budgets/{budget_id}", headers=headers)
    assert resp.status_code == 204
    assert client.get("/budgets", headers=headers).json() == []


def test_budget_list_includes_progress_fields(auth_client):
    client, headers, _ = auth_client
    client.post("/budgets", headers=headers, json={"category": "Food", "monthly_limit": 5000})
    resp = client.get("/budgets", headers=headers)
    body = resp.json()
    assert len(body) == 1
    assert set(body[0].keys()) >= {"category", "monthly_limit", "current_spend", "pct_used", "risk"}
