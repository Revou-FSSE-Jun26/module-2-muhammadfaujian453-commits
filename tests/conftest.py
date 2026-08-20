import pytest
from app import create_app
from utils import db

@pytest.fixture
def app():
    """Initializing Application for Testing"""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "JWT_SECRET_KEY": "This is the secret key for testing—minimum 32 characters."
    })

    # SQLite Database Setup in RAM
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Cloning Client for HTTP request (GET, POST, dll)"""
    return app.test_client()