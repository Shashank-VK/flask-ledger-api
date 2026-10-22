import re
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db
from app.models import User
from app.auth import generate_token

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be valid JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
        return jsonify({"error": "A valid email address is required"}), 400

    if not password or not isinstance(password, str):
        return jsonify({"error": "Password is required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    email_clean = email.strip().lower()

    existing_user = db.session.execute(
        db.select(User).filter_by(email=email_clean)
    ).scalar_one_or_none()
    if existing_user is not None:
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=email_clean)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be valid JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password are required"}), 400

    email_clean = email.strip().lower()
    user = db.session.execute(
        db.select(User).filter_by(email=email_clean)
    ).scalar_one_or_none()

    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(
        user_id=user.id,
        email=user.email,
        secret_key=current_app.config["SECRET_KEY"],
        expires_in=current_app.config["JWT_EXPIRATION_SECONDS"],
    )

    return jsonify({"access_token": token}), 200
