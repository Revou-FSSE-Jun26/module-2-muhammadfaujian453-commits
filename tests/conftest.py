import pytest
from app import create_app
from utils import db

@pytest.fixture(scope="session")
def app_instance():
    """Create the Flask instance once for the entire testing session."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "JWT_SECRET_KEY": "ini-adalah-kunci-rahasia-untuk-testing-minimal-32-karakter"
    })

    # SQLite Database Setup in RAM
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def app(app_instance):
    """Provide a pristine database context per test function using rollbacks."""
    with app_instance.app_context():
        yield app_instance
        # Rollback any changes made during an individual test
        db.session.rollback()
        # Explicitly clean up data from all tables without dropping them
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

@pytest.fixture
def client(app):
    """Cloning Client for HTTP request (GET, POST, dll)"""
    return app.test_client()