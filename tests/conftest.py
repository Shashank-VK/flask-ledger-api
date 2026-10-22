import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import User, Expense
from app.auth import generate_token

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    def _auth_headers(user):
        token = generate_token(
            user_id=user.id,
            email=user.email,
            secret_key=app.config["SECRET_KEY"],
            expires_in=app.config["JWT_EXPIRATION_SECONDS"],
        )
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers

@pytest.fixture
def user_a(app):
    with app.app_context():
        user = User(email="usera@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)

@pytest.fixture
def user_b(app):
    with app.app_context():
        user = User(email="userb@example.com")
        user.set_password("password456")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)
