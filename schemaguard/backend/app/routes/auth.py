"""Authentication routes - registration and login."""

from flask import Blueprint, abort, jsonify, request
from pydantic import ValidationError

from app.schemas.auth_schema import ForgotPasswordRequest, LoginRequest, RegisterRequest
from app.schemas.errors import format_validation_errors
from app.services.auth_service import (
    DuplicateEmailError,
    InvalidCredentialsError,
    login_user,
    request_password_reset,
    register_user,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    try:
        data = RegisterRequest.model_validate(request.get_json())
        response = register_user(data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    except DuplicateEmailError as error:
        abort(409, description=str(error))

    return jsonify(response.model_dump()), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT."""
    try:
        data = LoginRequest.model_validate(request.get_json())
        response = login_user(data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    except InvalidCredentialsError:
        abort(401)

    return jsonify(response.model_dump()), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Accept a password reset request."""
    try:
        data = ForgotPasswordRequest.model_validate(request.get_json())
        response = request_password_reset(data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))

    return jsonify(response), 200
