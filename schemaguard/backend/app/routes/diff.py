"""Diff routes — compare two specific schema versions."""

from flask import Blueprint, request, jsonify, abort

from app.middleware.auth_guard import jwt_required_custom
from app.services.registry_service import (
    get_registry,
    get_version,
    compare_versions,
    RegistryNotFoundError,
    VersionNotFoundError,
)
from app.services.activity_service import log_activity
from app.services.collaboration_service import ForbiddenRegistryAccessError, require_registry_role

diff_bp = Blueprint("diff", __name__, url_prefix="/api/diff")


@diff_bp.route("/<registry_id>", methods=["GET"])
@jwt_required_custom
def compare_two_versions(registry_id, current_user):
    """Compare two schema versions and return the diff result."""
    from_id = request.args.get("from")
    to_id = request.args.get("to")

    if not from_id or not to_id:
        abort(400, description="Both 'from' and 'to' query parameters are required")

    try:
        registry = get_registry(registry_id)
    except RegistryNotFoundError:
        abort(404)

    try:
        role = require_registry_role(registry, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    except ForbiddenRegistryAccessError:
        abort(403)

    try:
        from_version = get_version(from_id)
        to_version = get_version(to_id)
    except VersionNotFoundError:
        abort(404)

    if from_version.registry_id != registry.id or to_version.registry_id != registry.id:
        abort(404)

    result = compare_versions(from_version, to_version)
    log_activity(
        registry.id,
        current_user.email,
        role,
        "DIFF_VIEWED",
        {"from_version": from_version.version, "to_version": to_version.version},
    )
    return jsonify(result), 200
