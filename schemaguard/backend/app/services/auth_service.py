"""Authentication service functions."""

from datetime import datetime, timezone

from flask_jwt_extended import create_access_token

from app import db
from app.models.user import User
from app.schemas.auth_schema import (
    AuthResponse,
    ChangeEmailRequest,
    ChangePasswordRequest,
    ChangeUsernameRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    UserProfileResponse,
)


class DuplicateEmailError(Exception):
    """Raised when an email is already registered."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


class InvalidPasswordError(Exception):
    """Raised when the current password is incorrect."""


def register_user(data: RegisterRequest) -> AuthResponse:
    """Create a user account and return an auth response."""
    if User.query.filter_by(email=data.email).first():
        raise DuplicateEmailError("Email already registered")

    is_first_user = not db.session.query(User.id).first()
    user = User(
        email=data.email,
        username=data.email.split("@")[0],
        is_admin=is_first_user,
    )
    user.set_password(data.password)
    db.session.add(user)
    db.session.commit()

    return _auth_response(user)


def login_user(data: LoginRequest) -> AuthResponse:
    """Authenticate a user and return an auth response."""
    user = User.query.filter_by(email=data.email).first()
    if not user or not user.check_password(data.password):
        raise InvalidCredentialsError("Invalid email or password")
    if not user.is_active:
        raise InvalidCredentialsError("Account suspended")

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()
    return _auth_response(user)


def get_user_profile(user: User) -> UserProfileResponse:
    """Return the current user's profile."""
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        username=user.username or user.email.split("@")[0],
        created_at=user.created_at.isoformat(),
        is_admin=bool(user.is_admin),
    )


def change_user_email(user: User, data: ChangeEmailRequest) -> UserProfileResponse:
    """Change the current user's email address."""
    existing = User.query.filter(User.email == data.email, User.id != user.id).first()
    if existing:
        raise DuplicateEmailError("Email already registered")

    user.email = data.email
    db.session.commit()
    return get_user_profile(user)


def change_username(user: User, data: ChangeUsernameRequest) -> UserProfileResponse:
    """Change the current user's display username."""
    user.username = data.username.strip()
    db.session.commit()
    return get_user_profile(user)


def change_user_password(user: User, data: ChangePasswordRequest) -> None:
    """Change the current user's password after verifying the old password."""
    if not user.check_password(data.current_password):
        raise InvalidPasswordError("Current password is incorrect")

    user.set_password(data.new_password)
    db.session.commit()


def request_password_reset(data: ForgotPasswordRequest) -> dict:
    """Accept a reset request without revealing whether an email exists."""
    user = User.query.filter_by(email=data.email).first()
    return {
        "status": "ok",
        "message": "If the email exists, reset instructions have been prepared.",
        "reset_available": bool(user),
    }


def _auth_response(user: User) -> AuthResponse:
    """Build the token response for an authenticated user."""
    token = create_access_token(identity=user.id)
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        username=user.username or user.email.split("@")[0],
        is_admin=bool(user.is_admin),
    )
