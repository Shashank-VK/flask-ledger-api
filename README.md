# LedgerLite (flask-ledger-api)

A personal expense ledger REST API built with Flask. Users register, authenticate via JWT, and manage their own expenses categorized by label; a summary endpoint calculates aggregated monthly expenditure by category.

---

## Stack

- **Python**: 3.12
- **Web Framework**: Flask 3.x
- **ORM**: Flask-SQLAlchemy 3.x (SQLAlchemy 2.x style models and queries)
- **Authentication**: PyJWT (HMAC-SHA256 signed access tokens)
- **Password Hashing**: `werkzeug.security` (`generate_password_hash` / `check_password_hash`)
- **Database**: SQLite default (overridable via `DATABASE_URL` environment variable)
- **Testing**: pytest

---

## Setup

1. **Clone or navigate to the repository directory**:
   ```bash
   cd flask-ledger-api
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

You can start the development server using either the Flask CLI or the Python entrypoint:

```bash
flask --app app.py run
```

or:

```bash
python app.py
```

By default, the server runs on `http://127.0.0.1:5000`.

---

## Running Tests

Execute the test suite with pytest:

```bash
.venv/bin/python -m pytest
```

There are 34 tests in the suite covering registration, duplicate handling, login, authentication errors, JWT expiry, password security, expense CRUD, pagination bounds, cross-user isolation, and hand-computed summary calculations.

---

## API Endpoints

All error responses return a JSON body (`{"error": "<message>"}`) with the appropriate HTTP status code. HTML error pages are never returned.

| Method | Endpoint | Auth Required | Description | Request Body | Response Status & Body |
|---|---|---|---|---|---|
| `GET` | `/health` | No | Service health check | None | `200` `{"status": "ok"}` |
| `POST` | `/auth/register` | No | Register a new user | `{"email": "...", "password": "..."}` | `201` `{"id": <int>, "email": "<str>"}`<br>`409` if email is already registered<br>`400` on invalid payload |
| `POST` | `/auth/login` | No | Log in and obtain a JWT access token | `{"email": "...", "password": "..."}` | `200` `{"access_token": "<jwt>"}`<br>`401` on invalid credentials<br>`400` on invalid payload |
| `POST` | `/expenses` | Yes (`Bearer <token>`) | Create a new expense | `{"amount": <number>, "category": "<str>", "note": "<str>", "date": "YYYY-MM-DD"}` | `201` `{"id": <int>, "amount": <float>, "category": "<str>", "note": <str/null>, "date": "YYYY-MM-DD", "created_at": "...", "user_id": <int>}`<br>`400` on validation failure |
| `GET` | `/expenses` | Yes (`Bearer <token>`) | List caller's expenses (newest first, paginated) | Query params: `?page=1&per_page=10` | `200` `{"items": [...], "page": <int>, "per_page": <int>, "total": <int>, "pages": <int>}`<br>`400` on invalid pagination bounds |
| `GET` | `/expenses/<id>` | Yes (`Bearer <token>`) | Retrieve single expense by ID | None | `200` Expense object<br>`404` if not found or belongs to another user |
| `PUT` | `/expenses/<id>` | Yes (`Bearer <token>`) | Update fields on caller's expense | `{"amount": ..., "category": ..., "note": ..., "date": ...}` | `200` Updated expense object<br>`404` if not found or belongs to another user<br>`400` on invalid fields |
| `DELETE` | `/expenses/<id>` | Yes (`Bearer <token>`) | Delete caller's expense | None | `204 No Content`<br>`404` if not found or belongs to another user |
| `GET` | `/summary` | Yes (`Bearer <token>`) | Monthly aggregate spend for caller | Query params: `?month=YYYY-MM` | `200` `{"month": "YYYY-MM", "total": <float>, "by_category": {"<category>": <float>}}`<br>`400` on invalid month format or missing parameter |

---

## curl Walkthrough: Register -> Login -> Create Expense -> Summary

Here is a full end-to-end walkthrough using `curl`:

```bash
# 1. Register a new user
curl -s -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@example.com", "password": "securepassword123"}'

# Response:
# {"email":"jane@example.com","id":1}

# 2. Log in to obtain access token
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@example.com", "password": "securepassword123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 3. Create an expense
curl -s -X POST http://127.0.0.1:5000/expenses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 42.50, "category": "Groceries", "note": "Weekly produce", "date": "2026-05-10"}'

# Response:
# {"amount":42.5,"category":"Groceries","created_at":"2026-10-22T10:04:38.881953+00:00","date":"2026-05-10","id":1,"note":"Weekly produce","user_id":1}

# 4. View monthly expense summary
curl -s -X GET "http://127.0.0.1:5000/summary?month=2026-05" \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {"by_category":{"Groceries":42.5},"month":"2026-05","total":42.5}
```

---

## Notes & Configuration

- **JWT Expiry**:
  Access tokens expire by default after 86,400 seconds (24 hours). This duration can be configured via the `JWT_EXPIRATION_SECONDS` environment variable.
- **SQLite Default**:
  By default, data is stored locally in an SQLite database file at `instance/ledger.db`.
- **Security & Passwords**:
  Passwords are never stored in plaintext and are hashed using `werkzeug.security` with modern hashing algorithms (e.g., scrypt). Password hashes are never returned by any endpoint.
- **Cross-User Data Isolation**:
  Access to expenses and monthly summaries is strictly isolated per authenticated user ID. Requesting, modifying, or deleting an expense belonging to another user returns a `404 Not Found` response to avoid disclosing record existence.
- **Production Configuration**:
  When deploying beyond local development:
  1. Set `SECRET_KEY` in your environment to a secure, randomly generated string of at least 32 bytes (for example, generated via `python3 -c "import secrets; print(secrets.token_hex(32))"`). The application includes an explicit dev default for local testing.
  2. Set `DATABASE_URL` to point to a production-grade relational database URI (such as PostgreSQL: `postgresql://user:password@host:port/dbname`).
