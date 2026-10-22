def test_create_expense_happy_path(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    payload = {
        "amount": 42.50,
        "category": "Groceries",
        "note": "Weekly vegetables",
        "date": "2026-05-10",
    }
    response = client.post("/expenses", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.is_json
    data = response.get_json()
    assert data["amount"] == 42.50
    assert data["category"] == "Groceries"
    assert data["note"] == "Weekly vegetables"
    assert data["date"] == "2026-05-10"
    assert data["user_id"] == user_a.id
    assert "id" in data

def test_create_expense_without_optional_note(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    payload = {
        "amount": 15.0,
        "category": "Coffee",
        "date": "2026-05-11",
    }
    response = client.post("/expenses", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["note"] is None
    assert data["amount"] == 15.0

def test_create_expense_validation_negative_or_zero_amount(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    # Negative amount
    resp = client.post("/expenses", json={"amount": -10.0, "category": "Food", "date": "2026-05-10"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Zero amount
    resp = client.post("/expenses", json={"amount": 0, "category": "Food", "date": "2026-05-10"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

def test_create_expense_validation_non_numeric_amount(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    # String amount
    resp = client.post("/expenses", json={"amount": "forty", "category": "Food", "date": "2026-05-10"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Boolean amount (isinstance True is int in Python, but should be rejected)
    resp = client.post("/expenses", json={"amount": True, "category": "Food", "date": "2026-05-10"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

def test_create_expense_validation_missing_category(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    # Missing category
    resp = client.post("/expenses", json={"amount": 20.0, "date": "2026-05-10"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Empty string category
    resp = client.post("/expenses", json={"amount": 20.0, "category": "   ", "date": "2026-05-10"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

def test_create_expense_validation_bad_date_format(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    # Non-date string
    resp = client.post("/expenses", json={"amount": 20.0, "category": "Food", "date": "not-a-date"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Wrong format (DD-MM-YYYY)
    resp = client.post("/expenses", json={"amount": 20.0, "category": "Food", "date": "10-05-2026"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Missing date
    resp = client.post("/expenses", json={"amount": 20.0, "category": "Food"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

def test_get_single_expense_happy_path(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    created = client.post(
        "/expenses",
        json={"amount": 30.0, "category": "Books", "note": "Flask book", "date": "2026-05-01"},
        headers=headers,
    ).get_json()

    expense_id = created["id"]
    resp = client.get(f"/expenses/{expense_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == expense_id
    assert data["category"] == "Books"
    assert data["amount"] == 30.0

def test_get_single_expense_not_found(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    resp = client.get("/expenses/999999", headers=headers)
    assert resp.status_code == 404
    assert resp.is_json
    assert "error" in resp.get_json()

def test_update_expense_happy_path(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    created = client.post(
        "/expenses",
        json={"amount": 10.0, "category": "Snacks", "note": "Chips", "date": "2026-05-01"},
        headers=headers,
    ).get_json()

    expense_id = created["id"]
    update_payload = {
        "amount": 12.50,
        "category": "Snacks & Drinks",
        "note": "Chips and soda",
        "date": "2026-05-02",
    }
    resp = client.put(f"/expenses/{expense_id}", json=update_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == expense_id
    assert data["amount"] == 12.50
    assert data["category"] == "Snacks & Drinks"
    assert data["note"] == "Chips and soda"
    assert data["date"] == "2026-05-02"

def test_update_expense_validation_errors(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    created = client.post(
        "/expenses",
        json={"amount": 10.0, "category": "Snacks", "date": "2026-05-01"},
        headers=headers,
    ).get_json()
    expense_id = created["id"]

    # Negative amount update
    resp = client.put(f"/expenses/{expense_id}", json={"amount": -5.0}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Empty category update
    resp = client.put(f"/expenses/{expense_id}", json={"category": "   "}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Bad date update
    resp = client.put(f"/expenses/{expense_id}", json={"date": "bad-date"}, headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

def test_delete_expense_happy_path(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    created = client.post(
        "/expenses",
        json={"amount": 18.0, "category": "Lunch", "date": "2026-05-01"},
        headers=headers,
    ).get_json()
    expense_id = created["id"]

    # Delete
    del_resp = client.delete(f"/expenses/{expense_id}", headers=headers)
    assert del_resp.status_code == 204
    assert del_resp.data == b""

    # Confirm it's gone
    get_resp = client.get(f"/expenses/{expense_id}", headers=headers)
    assert get_resp.status_code == 404

def test_delete_expense_not_found(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    resp = client.delete("/expenses/888888", headers=headers)
    assert resp.status_code == 404
    assert resp.is_json

def test_list_expenses_order_and_pagination(client, auth_headers, user_a):
    headers = auth_headers(user_a)
    # Create 5 expenses on different dates
    dates = ["2026-05-01", "2026-05-05", "2026-05-12", "2026-05-18", "2026-05-25"]
    for d in dates:
        client.post(
            "/expenses",
            json={"amount": 10.0, "category": "Misc", "date": d},
            headers=headers,
        )

    # First page of 2 items
    resp = client.get("/expenses?page=1&per_page=2", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["pages"] == 3
    assert len(data["items"]) == 2
    # Newest first
    assert data["items"][0]["date"] == "2026-05-25"
    assert data["items"][1]["date"] == "2026-05-18"

    # Second page of 2 items
    resp2 = client.get("/expenses?page=2&per_page=2", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert len(data2["items"]) == 2
    assert data2["items"][0]["date"] == "2026-05-12"
    assert data2["items"][1]["date"] == "2026-05-05"

    # Third page of 1 item
    resp3 = client.get("/expenses?page=3&per_page=2", headers=headers)
    assert resp3.status_code == 200
    data3 = resp3.get_json()
    assert len(data3["items"]) == 1
    assert data3["items"][0]["date"] == "2026-05-01"

def test_list_expenses_pagination_bounds(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    # page < 1
    resp = client.get("/expenses?page=0", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    resp = client.get("/expenses?page=-1", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # per_page < 1
    resp = client.get("/expenses?per_page=0", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # per_page > 100
    resp = client.get("/expenses?per_page=101", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # non-integer page
    resp = client.get("/expenses?page=abc", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # non-integer per_page
    resp = client.get("/expenses?per_page=xyz", headers=headers)
    assert resp.status_code == 400
    assert "error" in resp.get_json()
