def test_summary_maths_on_seeded_data(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    # Seeded expenses for user_a in May 2026:
    # 1. Food: 25.50 on 2026-05-02
    # 2. Food: 14.25 on 2026-05-10
    # 3. Transport: 45.00 on 2026-05-15
    # 4. Utilities: 120.75 on 2026-05-20
    # 5. Food: 99.99 on 2026-06-01 (different month, MUST be excluded)
    # 6. Food: 10.00 on 2026-04-30 (different month, MUST be excluded)

    seeded_records = [
        {"amount": 25.50, "category": "Food", "date": "2026-05-02"},
        {"amount": 14.25, "category": "Food", "date": "2026-05-10"},
        {"amount": 45.00, "category": "Transport", "date": "2026-05-15"},
        {"amount": 120.75, "category": "Utilities", "date": "2026-05-20"},
        {"amount": 99.99, "category": "Food", "date": "2026-06-01"},
        {"amount": 10.00, "category": "Food", "date": "2026-04-30"},
    ]
    for r in seeded_records:
        res = client.post("/expenses", json=r, headers=headers)
        assert res.status_code == 201

    # Request summary for 2026-05
    resp = client.get("/summary?month=2026-05", headers=headers)
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()

    # Hand-computed calculations:
    # Food: 25.50 + 14.25 = 39.75
    # Transport: 45.00
    # Utilities: 120.75
    # Total: 39.75 + 45.00 + 120.75 = 205.50
    assert data["month"] == "2026-05"
    assert data["total"] == 205.50
    assert data["by_category"]["Food"] == 39.75
    assert data["by_category"]["Transport"] == 45.00
    assert data["by_category"]["Utilities"] == 120.75
    assert len(data["by_category"]) == 3

def test_summary_empty_month_returns_zeros(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    # Seed an expense in May 2026
    client.post(
        "/expenses",
        json={"amount": 50.0, "category": "Books", "date": "2026-05-01"},
        headers=headers,
    )

    # Check summary for month with no expenses
    resp = client.get("/summary?month=2026-08", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["month"] == "2026-08"
    assert data["total"] == 0.0
    assert data["by_category"] == {}

def test_summary_bad_month_formats_return_400(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    # Missing month param
    resp = client.get("/summary", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Month 13
    resp = client.get("/summary?month=2026-13", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Month 00
    resp = client.get("/summary?month=2026-00", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Incomplete format
    resp = client.get("/summary?month=2026-5", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Arbitrary string
    resp = client.get("/summary?month=invalid-month", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()
