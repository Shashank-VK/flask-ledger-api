import functools
from datetime import datetime, timezone, timedelta
from typing import Callable, Any
import jwt
from flask import request, jsonify, current_app, g

from app.extensions import db
from app.models import User

def generate_token(user_id: int, email: str, secret_key: str, expires_in: int = 86400) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

def decode_token(token: str, secret_key: str) -> dict:
    return jwt.decode(token, secret_key, algorithms=["HS256"])

def jwt_required(f: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401

        parts = auth_header.strip().split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format. Expected 'Bearer <token>'"}), 401

        token = parts[1]
        try:
            payload = decode_token(token, current_app.config["SECRET_KEY"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        sub = payload.get("sub")
        if not sub:
            return jsonify({"error": "Token payload missing subject"}), 401

        try:
            user_id = int(sub)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid token subject"}), 401

        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "User not found"}), 401

        g.current_user = user
        g.current_user_id = user.id
        return f(*args, **kwargs)

    return decorated_function
