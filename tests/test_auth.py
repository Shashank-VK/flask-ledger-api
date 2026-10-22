import time
from app.models import User
from app.extensions import db
from app.auth import generate_token

def test_register_happy_path(client, app):
    payload = {"email": "testuser@example.com", "password": "securepassword"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    assert response.is_json
    data = response.get_json()
    assert "id" in data
    assert data["email"] == "testuser@example.com"
    assert "password" not in data
    assert "password_hash" not in data

    # Verify password was hashed and saved in DB
    with app.app_context():
        user = db.session.execute(
            db.select(User).filter_by(email="testuser@example.com")
        ).scalar_one_or_none()
        assert user is not None
        assert user.password_hash != "securepassword"
        assert user.check_password("securepassword") is True
        assert user.check_password("wrongpassword") is False

def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    resp1 = client.post("/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/auth/register", json=payload)
    assert resp2.status_code == 409
    assert resp2.is_json
    data = resp2.get_json()
    assert "error" in data
    assert "already registered" in data["error"].lower()

def test_register_validation_errors(client):
    # Missing email
    resp = client.post("/auth/register", json={"password": "password123"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Invalid email format
    resp = client.post("/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Missing password
    resp = client.post("/auth/register", json={"email": "valid@example.com"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Password too short (< 6 chars)
    resp = client.post("/auth/register", json={"email": "valid@example.com", "password": "123"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Non-JSON payload
    resp = client.post("/auth/register", data="not-json", content_type="text/plain")
    assert resp.status_code == 400
    assert resp.is_json

def test_login_happy_path(client):
    # Register first
    client.post("/auth/register", json={"email": "loginuser@example.com", "password": "mypassword"})

    # Login
    resp = client.post("/auth/login", json={"email": "loginuser@example.com", "password": "mypassword"})
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 20

def test_login_bad_credentials(client):
    # User does not exist
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401
    assert resp.is_json
    assert "error" in resp.get_json()

    # Wrong password
    client.post("/auth/register", json={"email": "someone@example.com", "password": "correctpassword"})
    resp = client.post("/auth/login", json={"email": "someone@example.com", "password": "wrongpassword"})
    assert resp.status_code == 401
    assert resp.is_json
    assert "error" in resp.get_json()

def test_login_validation_errors(client):
    # Missing email
    resp = client.post("/auth/login", json={"password": "password123"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Missing password
    resp = client.post("/auth/login", json={"email": "someone@example.com"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

    # Non-JSON body
    resp = client.post("/auth/login", data="raw-body", content_type="text/plain")
    assert resp.status_code == 400
    assert resp.is_json

def test_unauthenticated_request_returns_401(client):
    resp = client.get("/expenses")
    assert resp.status_code == 401
    assert resp.is_json
    assert "error" in resp.get_json()

def test_invalid_token_returns_401(client):
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    resp = client.get("/expenses", headers=headers)
    assert resp.status_code == 401
    assert resp.is_json
    assert "error" in resp.get_json()

def test_malformed_auth_header_returns_401(client):
    headers = {"Authorization": "Basic something"}
    resp = client.get("/expenses", headers=headers)
    assert resp.status_code == 401
    assert resp.is_json
    assert "error" in resp.get_json()

def test_expired_token_returns_401(client, app, user_a):
    expired_token = generate_token(
        user_id=user_a.id,
        email=user_a.email,
        secret_key=app.config["SECRET_KEY"],
        expires_in=-10,  # Expired 10 seconds ago
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    resp = client.get("/expenses", headers=headers)
    assert resp.status_code == 401
    assert resp.is_json
    assert "error" in resp.get_json()
    assert "expired" in resp.get_json()["error"].lower()

def test_no_password_hash_leaked_in_any_response(client, auth_headers, user_a):
    headers = auth_headers(user_a)

    reg_resp = client.post("/auth/register", json={"email": "leakcheck@example.com", "password": "secret123password"})
    reg_text = reg_resp.get_data(as_text=True)
    assert "password_hash" not in reg_text
    assert "pbkdf2" not in reg_text
    assert "scrypt" not in reg_text

    login_resp = client.post("/auth/login", json={"email": "leakcheck@example.com", "password": "secret123password"})
    login_text = login_resp.get_data(as_text=True)
    assert "password_hash" not in login_text
    assert "pbkdf2" not in login_text
    assert "scrypt" not in login_text
