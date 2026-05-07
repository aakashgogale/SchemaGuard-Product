"""Test fixtures for SchemaGuard backend tests."""

import pytest
from app import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    """Create a Flask test app with SQLite in-memory DB."""
    app = create_app("testing")
    yield app


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """Provide a Flask test client."""
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def auth_headers(client):
    """Register and log in a test user, return JWT headers."""
    def _auth_headers(email="test@example.com", password="testpassword123"):
        # Register
        client.post("/api/auth/register", json={
            "email": email,
            "password": password,
        })
        # Login
        response = client.post("/api/auth/login", json={
            "email": email,
            "password": password,
        })
        data = response.get_json()
        return {
            "Authorization": f"Bearer {data['access_token']}",
            "Content-Type": "application/json",
        }
    return _auth_headers


@pytest.fixture
def sample_registry(client, auth_headers):
    """Create a sample registry for the test user."""
    headers = auth_headers()
    response = client.post("/api/registries", json={
        "name": "test-api",
        "description": "A test API registry",
    }, headers=headers)
    data = response.get_json()
    return data, headers


@pytest.fixture
def sample_schema_v1():
    """Return a sample v1 schema for testing."""
    return {
        "properties": {
            "user_id": {"type": "string"},
            "amount": {"type": "integer"},
        },
        "required": ["user_id"],
    }


@pytest.fixture
def sample_schema_v2():
    """Return a sample v2 schema with breaking and safe changes."""
    return {
        "properties": {
            "user_id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
        },
        "required": ["user_id"],
    }
