"""Pytest configuration and test fixtures for Beyond Horizons."""
import pytest
from backend.app import create_app
from backend.database import init_db, close_db, get_db


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure every test uses a fresh in-memory mock database."""
    init_db(force_mock=True, db_name="beyond_horizons_test")
    db = get_db()
    if db is not None:
        db.users.delete_many({})
        db.trips.delete_many({})
    yield
    close_db()


@pytest.fixture
def app():
    """Create test application instance."""
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-for-beyond-horizons",
        "SESSION_COOKIE_SECURE": False,
    })
    return test_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


class AuthHelper:
    """Helper methods for authentication in tests."""

    def __init__(self, client):
        self.client = client

    def register(self, name="Aanya Sharma", email="aanya@example.com", password="SecurePassword123!", confirm=None):
        if confirm is None:
            confirm = password
        return self.client.post("/api/auth/register", json={
            "name": name,
            "email": email,
            "password": password,
            "confirmPassword": confirm
        })

    def login(self, email="aanya@example.com", password="SecurePassword123!"):
        return self.client.post("/api/auth/login", json={
            "email": email,
            "password": password
        })

    def logout(self):
        return self.client.post("/api/auth/logout")


@pytest.fixture
def auth(client):
    """Provide authentication helper."""
    return AuthHelper(client)
