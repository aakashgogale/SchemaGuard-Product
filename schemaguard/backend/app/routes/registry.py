"""Registry routes — CRUD operations for API registries."""

from flask import Blueprint, request, jsonify, abort
from pydantic import ValidationError

from app.middleware.auth_guard import jwt_required_custom
from app.schemas.errors import format_validation_errors
from app.schemas.registry_schema import CreateRegistryRequest
from app.services.registry_service import (
    create_registry,
    list_registries,
    get_registry,
    get_registry_response,
    delete_registry,
    DuplicateRegistryError,
    RegistryNotFoundError,
)
from app.services.collaboration_service import ForbiddenRegistryAccessError, require_registry_role

registry_bp = Blueprint("registry", __name__, url_prefix="/api/registries")


@registry_bp.route("", methods=["GET"])
@jwt_required_custom
def list_user_registries(current_user):
    """List all registries owned by the authenticated user."""
    result = list_registries(current_user)
    return jsonify(result.model_dump()), 200


@registry_bp.route("", methods=["POST"])
@jwt_required_custom
def create_new_registry(current_user):
    """Create a new API registry."""
    try:
        data = CreateRegistryRequest.model_validate(request.get_json())
    except ValidationError as e:
        abort(422, description=format_validation_errors(e))

    try:
        response = create_registry(current_user, data)
    except DuplicateRegistryError as e:
        abort(409, description=str(e))

    return jsonify(response.model_dump()), 201


@registry_bp.route("/<registry_id>", methods=["GET"])
@jwt_required_custom
def get_single_registry(registry_id, current_user):
    """Get a single registry with its versions."""
    try:
        registry = get_registry(registry_id)
    except RegistryNotFoundError:
        abort(404)

    try:
        require_registry_role(registry, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    except ForbiddenRegistryAccessError:
        abort(403)

    return jsonify(get_registry_response(registry)), 200


@registry_bp.route("/<registry_id>", methods=["DELETE"])
@jwt_required_custom
def delete_single_registry(registry_id, current_user):
    """Delete a registry and all its versions."""
    try:
        registry = get_registry(registry_id)
    except RegistryNotFoundError:
        abort(404)

    if registry.owner_id != current_user.id:
        abort(403)

    delete_registry(registry)
    return "", 204
