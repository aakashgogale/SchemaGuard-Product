"""Profile routes for current-user account management."""

from flask import Blueprint, abort, jsonify, request
from pydantic import ValidationError

from app.middleware.auth_guard import jwt_required_custom
from app.schemas.auth_schema import ChangeEmailRequest, ChangePasswordRequest, ChangeUsernameRequest
from app.schemas.errors import format_validation_errors
from app.services.auth_service import (
    DuplicateEmailError,
    InvalidPasswordError,
    change_user_email,
    change_user_password,
    change_username,
    get_user_profile,
)

profile_bp = Blueprint("profile", __name__, url_prefix="/api/me")


@profile_bp.route("", methods=["GET"])
@jwt_required_custom
def current_profile(current_user):
    """Return the current authenticated user's profile."""
    return jsonify(get_user_profile(current_user).model_dump()), 200


@profile_bp.route("/email", methods=["PATCH"])
@jwt_required_custom
def update_email(current_user):
    """Update the current user's email address."""
    try:
        data = ChangeEmailRequest.model_validate(request.get_json())
        profile = change_user_email(current_user, data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    except DuplicateEmailError as error:
        abort(409, description=str(error))

    return jsonify(profile.model_dump()), 200


@profile_bp.route("/username", methods=["PATCH"])
@jwt_required_custom
def update_username(current_user):
    """Update the current user's display username."""
    try:
        data = ChangeUsernameRequest.model_validate(request.get_json())
        profile = change_username(current_user, data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))

    return jsonify(profile.model_dump()), 200


@profile_bp.route("/password", methods=["POST"])
@jwt_required_custom
def update_password(current_user):
    """Update the current user's password."""
    try:
        data = ChangePasswordRequest.model_validate(request.get_json())
        change_user_password(current_user, data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    except InvalidPasswordError as error:
        abort(401, description=str(error))

    return jsonify({"status": "ok", "message": "Password updated"}), 200
