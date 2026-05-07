"""Tests for API routes — 10 test cases covering success and failure paths."""


def test_register_new_user_returns_201(client):
    """Registering a new user should return 201 with a token."""
    response = client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "password": "securepassword123",
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "access_token" in data
    assert data["email"] == "newuser@example.com"
    assert "user_id" in data


def test_register_duplicate_email_returns_409(client):
    """Registering with an existing email should return 409."""
    payload = {"email": "dupe@example.com", "password": "securepassword123"}
    client.post("/api/auth/register", json=payload)
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    data = response.get_json()
    assert data["error"] == "conflict"


def test_login_valid_credentials_returns_token(client):
    """Logging in with valid credentials should return a token."""
    client.post("/api/auth/register", json={
        "email": "loginuser@example.com",
        "password": "securepassword123",
    })
    response = client.post("/api/auth/login", json={
        "email": "loginuser@example.com",
        "password": "securepassword123",
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data


def test_login_invalid_password_returns_401(client):
    """Logging in with wrong password should return 401."""
    client.post("/api/auth/register", json={
        "email": "wrongpw@example.com",
        "password": "securepassword123",
    })
    response = client.post("/api/auth/login", json={
        "email": "wrongpw@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_create_registry_authenticated_returns_201(client, auth_headers):
    """Creating a registry while authenticated should return 201."""
    headers = auth_headers()
    response = client.post("/api/registries", json={
        "name": "my-api",
        "description": "My test API",
    }, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "my-api"
    assert "id" in data


def test_create_registry_unauthenticated_returns_401(client):
    """Creating a registry without auth should return 401."""
    response = client.post("/api/registries", json={
        "name": "my-api",
        "description": "My test API",
    })
    assert response.status_code == 401


def test_upload_version_triggers_diff_engine(client, sample_registry, sample_schema_v1, sample_schema_v2):
    """Uploading a second version should trigger the diff engine."""
    registry, headers = sample_registry

    # Upload v1
    client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "1.0.0",
        "schema_json": sample_schema_v1,
    }, headers=headers)

    # Upload v2
    response = client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "2.0.0",
        "schema_json": sample_schema_v2,
    }, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["diff_result"] is not None
    assert data["diff_result"]["is_breaking"] is True


def test_upload_duplicate_version_returns_409(client, sample_registry, sample_schema_v1):
    """Uploading a version that already exists should return 409."""
    registry, headers = sample_registry

    client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "1.0.0",
        "schema_json": sample_schema_v1,
    }, headers=headers)

    response = client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "1.0.0",
        "schema_json": sample_schema_v1,
    }, headers=headers)
    assert response.status_code == 409


def test_diff_endpoint_returns_correct_breaking_count(client, sample_registry, sample_schema_v1, sample_schema_v2):
    """The diff endpoint should return the correct number of breaking changes."""
    registry, headers = sample_registry

    # Upload v1
    v1_response = client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "1.0.0",
        "schema_json": sample_schema_v1,
    }, headers=headers)
    v1_id = v1_response.get_json()["id"]

    # Upload v2
    v2_response = client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "2.0.0",
        "schema_json": sample_schema_v2,
    }, headers=headers)
    v2_id = v2_response.get_json()["id"]

    # Compare
    response = client.get(
        f"/api/diff/{registry['id']}?from={v1_id}&to={v2_id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["is_breaking"] is True
    assert data["breaking_count"] >= 1


def test_health_endpoint_returns_ok(client):
    """The health endpoint should return ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"
    assert "timestamp" in data


def test_version_response_includes_schema_json(client, sample_registry, sample_schema_v1):
    """Version responses should include schema_json for frontend diff rendering."""
    registry, headers = sample_registry
    response = client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "1.0.0",
        "schema_json": sample_schema_v1,
    }, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["schema_json"] == sample_schema_v1


def test_status_transition_allowed_sequence(db, sample_registry, sample_schema_v1):
    """Service layer should allow PENDING to ACTIVE to DEPRECATED."""
    from app.models.version import SchemaVersion, VersionStatus
    from app.services.registry_service import transition_version_status

    registry, _headers = sample_registry
    version = SchemaVersion(
        registry_id=registry["id"],
        version="1.0.0",
        schema_json=sample_schema_v1,
    )
    db.session.add(version)
    db.session.commit()

    active = transition_version_status(version, VersionStatus.ACTIVE)
    assert active.status == "ACTIVE"
    deprecated = transition_version_status(version, VersionStatus.DEPRECATED)
    assert deprecated.status == "DEPRECATED"


def test_status_transition_rejects_invalid_move(db, sample_registry, sample_schema_v1):
    """Service layer should reject status moves outside the allowed graph."""
    import pytest
    from app.models.version import SchemaVersion, VersionStatus
    from app.services.registry_service import (
        InvalidStatusTransitionError,
        transition_version_status,
    )

    registry, _headers = sample_registry
    version = SchemaVersion(
        registry_id=registry["id"],
        version="1.0.0",
        schema_json=sample_schema_v1,
    )
    db.session.add(version)
    db.session.commit()

    with pytest.raises(InvalidStatusTransitionError):
        transition_version_status(version, VersionStatus.DEPRECATED)


def test_add_member_and_duplicate_returns_409(client, sample_registry):
    """Registry owners can add members, but not duplicate emails."""
    registry, headers = sample_registry
    payload = {"email": "teammate@example.com"}
    response = client.post(
        f"/api/registries/{registry['id']}/members", json=payload, headers=headers
    )
    assert response.status_code == 201
    assert response.get_json()["email"] == payload["email"]

    duplicate = client.post(
        f"/api/registries/{registry['id']}/members", json=payload, headers=headers
    )
    assert duplicate.status_code == 409


def test_add_subscriber_with_webhook_returns_201(client, sample_registry):
    """Registry owners can add subscribers with optional Slack webhooks."""
    registry, headers = sample_registry
    response = client.post(
        f"/api/registries/{registry['id']}/subscribers",
        json={
            "email": "consumer@example.com",
            "webhook_url": "https://hooks.slack.com/services/T000/B000/xxx",
            "notify_breaking_only": False,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["email"] == "consumer@example.com"
    assert data["notify_breaking_only"] is False


def test_upload_version_stores_change_reason(client, sample_registry, sample_schema_v1):
    """Uploaded versions should persist the optional change reason."""
    registry, headers = sample_registry
    response = client.post(
        f"/api/registries/{registry['id']}/versions",
        json={
            "version": "1.0.0",
            "schema_json": sample_schema_v1,
            "change_reason": "Initial contract",
        },
        headers=headers,
    )
    assert response.status_code == 201
    assert response.get_json()["change_reason"] == "Initial contract"


def test_public_diff_endpoint_returns_latest_diff(client, sample_registry, sample_schema_v1, sample_schema_v2):
    """Public diff endpoint should expose latest diff without auth."""
    registry, headers = sample_registry
    client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "1.0.0",
        "schema_json": sample_schema_v1,
    }, headers=headers)
    client.post(f"/api/registries/{registry['id']}/versions", json={
        "version": "2.0.0",
        "schema_json": sample_schema_v2,
        "change_reason": "Amount supports decimals",
    }, headers=headers)
    detail = client.get(f"/api/registries/{registry['id']}", headers=headers).get_json()

    response = client.get(f"/public/diff/{detail['public_token']}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["registry_name"] == registry["name"]
    assert data["version"] == "2.0.0"
    assert data["change_reason"] == "Amount supports decimals"
    assert data["diff_result"]["is_breaking"] is True


def test_agent_chat_without_api_key_uses_local_context(client, auth_headers):
    """Agent chat should still answer from local context when no provider key is configured."""
    headers = auth_headers()
    response = client.post(
        "/api/agent/chat",
        json={"message": "Is it safe to deploy?"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["used_context"] is True
    assert "reply" in data


def test_dashboard_stats_returns_user_context_counts(client, sample_registry, sample_schema_v1):
    """Dashboard stats should expose context counts for the agent sidebar."""
    registry, headers = sample_registry
    client.post(
        f"/api/registries/{registry['id']}/versions",
        json={"version": "1.0.0", "schema_json": sample_schema_v1},
        headers=headers,
    )
    response = client.get("/api/dashboard/stats", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_apis"] == 1
    assert data["total_versions"] == 1
