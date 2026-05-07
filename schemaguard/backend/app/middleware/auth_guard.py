"""Authentication guard middleware — centralized JWT logic."""

from functools import wraps

from flask import abort
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app import db
from app.models.user import User


def get_current_user() -> User:
    """Extract and validate JWT, return the authenticated User object."""
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if user is None:
        abort(401)
    if not user.is_active:
        abort(403, description="Account suspended")
    return user


def require_owner(resource_owner_id: str) -> None:
    """Verify the current user owns the resource, raise 403 if not."""
    user = get_current_user()
    if user.id != resource_owner_id:
        abort(403)


def jwt_required_custom(fn):
    """Decorator that ensures a valid JWT is present and loads the user."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        kwargs["current_user"] = user
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Decorator that requires an active admin user."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user.is_admin:
            abort(403)
        kwargs["current_user"] = user
        return fn(*args, **kwargs)
    return wrapper
