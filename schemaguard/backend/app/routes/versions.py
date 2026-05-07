"""Version routes — upload and list schema versions."""

from flask import Blueprint, current_app, request, jsonify, abort
from pydantic import ValidationError

from app.middleware.auth_guard import jwt_required_custom
from app.schemas.errors import format_validation_errors
from app.schemas.version_schema import UploadVersionRequest
from app.services.registry_service import (
    get_registry,
    upload_version,
    list_versions,
    get_version,
    DuplicateVersionError,
    RegistryNotFoundError,
    VersionNotFoundError,
)
from app.services.collaboration_service import ForbiddenRegistryAccessError, require_registry_role

versions_bp = Blueprint("versions", __name__, url_prefix="/api/registries")


@versions_bp.route("/<registry_id>/versions", methods=["POST"])
@jwt_required_custom
def upload_new_version(registry_id, current_user):
    """Upload a new schema version for a registry."""
    try:
        registry = get_registry(registry_id)
    except RegistryNotFoundError:
        abort(404)

    try:
        require_registry_role(registry, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    except ForbiddenRegistryAccessError:
        abort(403)

    try:
        data = UploadVersionRequest.model_validate(request.get_json())
    except ValidationError as e:
        abort(422, description=format_validation_errors(e))

    try:
        notification_config = {
            "SMTP_HOST": current_app.config.get("SMTP_HOST"),
            "SMTP_PORT": current_app.config.get("SMTP_PORT"),
            "SMTP_USE_TLS": current_app.config.get("SMTP_USE_TLS"),
            "SMTP_USERNAME": current_app.config.get("SMTP_USERNAME"),
            "SMTP_PASSWORD": current_app.config.get("SMTP_PASSWORD"),
            "SMTP_FROM_EMAIL": current_app.config.get("SMTP_FROM_EMAIL"),
            "FRONTEND_URL": current_app.config.get("FRONTEND_URL"),
        }
        response = upload_version(registry, data, current_user, notification_config)
    except DuplicateVersionError as e:
        abort(409, description=str(e))

    return jsonify(response.model_dump()), 201


@versions_bp.route("/<registry_id>/versions", methods=["GET"])
@jwt_required_custom
def list_registry_versions(registry_id, current_user):
    """List all versions for a registry."""
    try:
        registry = get_registry(registry_id)
    except RegistryNotFoundError:
        abort(404)

    try:
        require_registry_role(registry, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    except ForbiddenRegistryAccessError:
        abort(403)

    versions = list_versions(registry)
    return jsonify([v.model_dump() for v in versions]), 200


@versions_bp.route("/<registry_id>/versions/<version_id>", methods=["GET"])
@jwt_required_custom
def get_single_version(registry_id, version_id, current_user):
    """Get a single version by ID."""
    try:
        registry = get_registry(registry_id)
    except RegistryNotFoundError:
        abort(404)

    try:
        require_registry_role(registry, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    except ForbiddenRegistryAccessError:
        abort(403)

    try:
        version = get_version(version_id)
    except VersionNotFoundError:
        abort(404)

    if version.registry_id != registry.id:
        abort(404)

    from app.schemas.version_schema import VersionResponse
    response = VersionResponse(
        id=version.id,
        version=version.version,
        status=version.status.value,
        schema_json=version.schema_json,
        change_reason=version.change_reason,
        diff_result=version.diff_result,
        uploaded_at=version.uploaded_at,
    )
    return jsonify(response.model_dump()), 200
