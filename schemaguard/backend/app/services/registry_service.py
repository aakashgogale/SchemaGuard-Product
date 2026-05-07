"""Registry service — business logic for API registries and versions."""

from __future__ import annotations

import threading

from app import db
from app.models.registry import APIRegistry
from app.models.version import SchemaVersion, VersionStatus
from app.models.user import User
from app.schemas.registry_schema import CreateRegistryRequest, RegistryResponse, RegistryListResponse
from app.schemas.version_schema import UploadVersionRequest, VersionResponse
from app.services.activity_service import log_activity
from app.services.diff_engine import compare_schemas, DiffResult


class DuplicateRegistryError(Exception):
    """Raised when a registry with the same name already exists for the user."""
    pass


class DuplicateVersionError(Exception):
    """Raised when a version already exists for the registry."""
    pass


class RegistryNotFoundError(Exception):
    """Raised when a registry is not found."""
    pass


class VersionNotFoundError(Exception):
    """Raised when a version is not found."""
    pass


class InvalidStatusTransitionError(Exception):
    """Raised when a schema version status transition is invalid."""

    def __init__(self, from_status: VersionStatus, to_status: VersionStatus):
        """Create a transition error with source and target statuses."""
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            f"Invalid status transition: {from_status.value} -> {to_status.value}"
        )


VALID_STATUS_TRANSITIONS = {
    VersionStatus.PENDING: {VersionStatus.ACTIVE},
    VersionStatus.ACTIVE: {VersionStatus.DEPRECATED},
    VersionStatus.DEPRECATED: set(),
}


def create_registry(user: User, data: CreateRegistryRequest) -> RegistryResponse:
    """Create a new API registry for the given user."""
    existing = APIRegistry.query.filter_by(owner_id=user.id, name=data.name).first()
    if existing:
        raise DuplicateRegistryError(f"Registry '{data.name}' already exists")

    registry = APIRegistry(
        owner_id=user.id,
        name=data.name,
        description=data.description,
    )
    db.session.add(registry)
    db.session.commit()
    log_activity(
        registry.id,
        user.email,
        "OWNER",
        "REGISTRY_CREATED",
        {"registry_name": registry.name},
    )

    return _registry_to_response(registry)


def list_registries(user: User) -> RegistryListResponse:
    """List all registries owned by or shared with the given user."""
    owned = APIRegistry.query.filter_by(owner_id=user.id).all()
    member_ids = [
        item.registry_id for item in getattr(user, "_member_rows", [])
    ]
    try:
        from app.models.collaboration import APIMember

        member_ids = [
            item.registry_id
            for item in APIMember.query.filter_by(email=user.email).all()
        ]
    except Exception:
        member_ids = []
    shared = APIRegistry.query.filter(APIRegistry.id.in_(member_ids)).all() if member_ids else []
    registries = list({registry.id: registry for registry in [*owned, *shared]}.values())
    items = [_registry_to_response(r) for r in registries]
    return RegistryListResponse(registries=items, total=len(items))


def get_registry(registry_id: str) -> APIRegistry:
    """Retrieve a registry by ID, raise RegistryNotFoundError if missing."""
    registry = db.session.get(APIRegistry, registry_id)
    if registry is None:
        raise RegistryNotFoundError(f"Registry {registry_id} not found")
    return registry


def get_registry_response(registry: APIRegistry) -> dict:
    """Build a full registry response with versions list."""
    response = _registry_to_response(registry).model_dump()
    response["versions"] = [
        _version_to_response(v).model_dump() for v in registry.versions
    ]
    return response


def delete_registry(registry: APIRegistry) -> None:
    """Delete a registry and all its versions."""
    name = registry.name
    owner_email = registry.owner.email if registry.owner else "unknown"
    registry_id = registry.id
    db.session.delete(registry)
    db.session.commit()
    log_activity(registry_id, owner_email, "OWNER", "REGISTRY_DELETED", {"registry_name": name})


def upload_version(
    registry: APIRegistry,
    data: UploadVersionRequest,
    uploaded_by: User | None = None,
    notification_config: dict | None = None,
) -> VersionResponse:
    """Upload a new schema version and run diff against the previous version."""
    existing = SchemaVersion.query.filter_by(
        registry_id=registry.id, version=data.version
    ).first()
    if existing:
        raise DuplicateVersionError(f"Version {data.version} already exists")

    # Find the previous version for diffing
    previous = (
        SchemaVersion.query
        .filter_by(registry_id=registry.id)
        .order_by(SchemaVersion.uploaded_at.desc())
        .first()
    )

    # Run diff engine
    diff_result: DiffResult | None = None
    if previous:
        diff_result = compare_schemas(previous.schema_json, data.schema_data)

    version = SchemaVersion(
        registry_id=registry.id,
        uploaded_by_id=uploaded_by.id if uploaded_by else None,
        version=data.version,
        schema_json=data.schema_data,
        change_reason=data.change_reason,
        diff_result=diff_result.to_dict() if diff_result else None,
    )
    db.session.add(version)
    if uploaded_by:
        uploaded_by.total_uploads = (uploaded_by.total_uploads or 0) + 1
    db.session.commit()
    db.session.refresh(version)

    if uploaded_by and notification_config:
        _start_notification_thread(registry, version, uploaded_by, notification_config)
    if uploaded_by:
        log_activity(
            registry.id,
            uploaded_by.email,
            "OWNER" if registry.owner_id == uploaded_by.id else "MEMBER",
            "SCHEMA_UPLOADED",
            {
                "version": version.version,
                "breaking_count": (version.diff_result or {}).get("breaking_count", 0),
                "safe_count": (version.diff_result or {}).get("safe_count", 0),
            },
        )

    return _version_to_response(version)


def list_versions(registry: APIRegistry) -> list[VersionResponse]:
    """List all versions for a registry."""
    return [_version_to_response(v) for v in registry.versions]


def get_version(version_id: str) -> SchemaVersion:
    """Retrieve a version by ID."""
    version = db.session.get(SchemaVersion, version_id)
    if version is None:
        raise VersionNotFoundError(f"Version {version_id} not found")
    return version


def transition_version_status(
    version: SchemaVersion, new_status: VersionStatus
) -> VersionResponse:
    """Transition a version status when the requested move is allowed."""
    if new_status not in VALID_STATUS_TRANSITIONS.get(version.status, set()):
        raise InvalidStatusTransitionError(version.status, new_status)

    version.status = new_status
    db.session.commit()
    return _version_to_response(version)


def compare_versions(from_version: SchemaVersion, to_version: SchemaVersion) -> dict:
    """Compare two specific versions and return the diff result."""
    result = compare_schemas(from_version.schema_json, to_version.schema_json)
    return result.to_dict()


def _registry_to_response(registry: APIRegistry) -> RegistryResponse:
    """Convert a registry model to a response schema."""
    return RegistryResponse(
        id=registry.id,
        name=registry.name,
        description=registry.description,
        public_token=registry.public_token,
        created_at=registry.created_at,
        version_count=len(registry.versions),
    )


def _version_to_response(version: SchemaVersion) -> VersionResponse:
    """Convert a version model to a response schema."""
    return VersionResponse(
        id=version.id,
        version=version.version,
        status=version.status.value,
        schema_json=version.schema_json,
        change_reason=version.change_reason,
        diff_result=version.diff_result,
        uploaded_at=version.uploaded_at,
    )


def _start_notification_thread(
    registry: APIRegistry,
    version: SchemaVersion,
    uploaded_by: User,
    config: dict,
) -> None:
    """Start a daemon notification worker for a saved schema version."""
    from app.services.notification_service import notify_schema_change

    frontend_url = config.get("FRONTEND_URL", "http://localhost:3001").rstrip("/")
    diff_result = version.diff_result or {
        "is_breaking": False,
        "breaking_count": 0,
        "safe_count": 0,
        "total_changes": 0,
        "changes": [],
    }
    payload = {
        "api_name": registry.name,
        "version": version.version,
        "uploaded_by": uploaded_by.email,
        "change_reason": version.change_reason,
        "is_breaking": bool(diff_result.get("is_breaking")),
        "changes": diff_result.get("changes", []),
        "members": [{"email": member.email} for member in registry.members],
        "subscribers": [
            {
                "email": subscriber.email,
                "webhook_url": subscriber.webhook_url,
                "notify_breaking_only": subscriber.notify_breaking_only,
            }
            for subscriber in registry.subscribers
        ],
        "dashboard_url": f"{frontend_url}/api/{registry.id}",
        "public_diff_url": f"{frontend_url}/public/diff/{registry.public_token}",
    }
    thread = threading.Thread(
        target=notify_schema_change,
        args=(payload, dict(config)),
        daemon=True,
    )
    thread.start()
