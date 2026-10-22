def test_user_b_cannot_read_user_a_expense(client, auth_headers, user_a, user_b):
    headers_a = auth_headers(user_a)
    headers_b = auth_headers(user_b)

    # User A creates an expense
    create_resp = client.post(
        "/expenses",
        json={"amount": 99.99, "category": "Personal", "note": "Confidential A", "date": "2026-05-15"},
        headers=headers_a,
    )
    assert create_resp.status_code == 201
    expense_id = create_resp.get_json()["id"]

    # User A can read it
    read_a = client.get(f"/expenses/{expense_id}", headers=headers_a)
    assert read_a.status_code == 200

    # User B receives 404 when trying to read User A's expense
    read_b = client.get(f"/expenses/{expense_id}", headers=headers_b)
    assert read_b.status_code == 404
    assert read_b.is_json
    assert "not found" in read_b.get_json()["error"].lower()

def test_user_b_cannot_update_user_a_expense(client, auth_headers, user_a, user_b):
    headers_a = auth_headers(user_a)
    headers_b = auth_headers(user_b)

    # User A creates an expense
    create_resp = client.post(
        "/expenses",
        json={"amount": 50.0, "category": "Travel", "date": "2026-05-16"},
        headers=headers_a,
    )
    expense_id = create_resp.get_json()["id"]

    # User B attempts to update User A's expense -> 404
    update_b = client.put(
        f"/expenses/{expense_id}",
        json={"amount": 1.0, "category": "Hacked"},
        headers=headers_b,
    )
    assert update_b.status_code == 404
    assert update_b.is_json

    # Verify User A's expense was NOT modified
    verify_a = client.get(f"/expenses/{expense_id}", headers=headers_a)
    assert verify_a.status_code == 200
    assert verify_a.get_json()["amount"] == 50.0
    assert verify_a.get_json()["category"] == "Travel"

def test_user_b_cannot_delete_user_a_expense(client, auth_headers, user_a, user_b):
    headers_a = auth_headers(user_a)
    headers_b = auth_headers(user_b)

    # User A creates an expense
    create_resp = client.post(
        "/expenses",
        json={"amount": 75.0, "category": "Equipment", "date": "2026-05-17"},
        headers=headers_a,
    )
    expense_id = create_resp.get_json()["id"]

    # User B attempts to delete User A's expense -> 404
    del_b = client.delete(f"/expenses/{expense_id}", headers=headers_b)
    assert del_b.status_code == 404

    # Verify User A's expense still exists
    verify_a = client.get(f"/expenses/{expense_id}", headers=headers_a)
    assert verify_a.status_code == 200
    assert verify_a.get_json()["amount"] == 75.0

def test_list_shows_only_own_expenses(client, auth_headers, user_a, user_b):
    headers_a = auth_headers(user_a)
    headers_b = auth_headers(user_b)

    # User A creates 2 expenses
    client.post("/expenses", json={"amount": 10.0, "category": "A1", "date": "2026-05-01"}, headers=headers_a)
    client.post("/expenses", json={"amount": 20.0, "category": "A2", "date": "2026-05-02"}, headers=headers_a)

    # User B creates 1 expense
    client.post("/expenses", json={"amount": 99.0, "category": "B1", "date": "2026-05-03"}, headers=headers_b)

    # User A lists expenses
    resp_a = client.get("/expenses", headers=headers_a)
    assert resp_a.status_code == 200
    data_a = resp_a.get_json()
    assert data_a["total"] == 2
    categories_a = [item["category"] for item in data_a["items"]]
    assert categories_a == ["A2", "A1"]
    assert "B1" not in categories_a

    # User B lists expenses
    resp_b = client.get("/expenses", headers=headers_b)
    assert resp_b.status_code == 200
    data_b = resp_b.get_json()
    assert data_b["total"] == 1
    assert data_b["items"][0]["category"] == "B1"
    assert "A1" not in [item["category"] for item in data_b["items"]]
    assert "A2" not in [item["category"] for item in data_b["items"]]

def test_summary_never_mixes_users(client, auth_headers, user_a, user_b):
    headers_a = auth_headers(user_a)
    headers_b = auth_headers(user_b)

    # User A expenses in 2026-05: 100.00 + 50.00 = 150.00
    client.post("/expenses", json={"amount": 100.00, "category": "Rent", "date": "2026-05-01"}, headers=headers_a)
    client.post("/expenses", json={"amount": 50.00, "category": "Groceries", "date": "2026-05-15"}, headers=headers_a)

    # User B expenses in 2026-05: 75.25
    client.post("/expenses", json={"amount": 75.25, "category": "Utilities", "date": "2026-05-10"}, headers=headers_b)

    # Summary for User A
    sum_a = client.get("/summary?month=2026-05", headers=headers_a).get_json()
    assert sum_a["total"] == 150.00
    assert sum_a["by_category"] == {"Rent": 100.00, "Groceries": 50.00}
    assert "Utilities" not in sum_a["by_category"]

    # Summary for User B
    sum_b = client.get("/summary?month=2026-05", headers=headers_b).get_json()
    assert sum_b["total"] == 75.25
    assert sum_b["by_category"] == {"Utilities": 75.25}
    assert "Rent" not in sum_b["by_category"]
    assert "Groceries" not in sum_b["by_category"]
