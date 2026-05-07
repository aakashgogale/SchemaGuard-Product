"""Admin routes for platform-wide management."""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, abort, jsonify
from app import db
from app.middleware.auth_guard import admin_required
from app.models.registry import APIRegistry
from app.models.user import User
from app.models.version import SchemaVersion

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _aware(value):
    """Ensure datetimes compare as UTC aware values."""
    if value and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _activity_status(user: User) -> str:
    """Compute a user's activity status server-side."""
    if not user.is_active:
        return "suspended"
    last_active = _aware(user.last_active_at)
    if not last_active:
        return "never"
    age = datetime.now(timezone.utc) - last_active
    if age <= timedelta(minutes=5):
        return "online"
    if age <= timedelta(hours=2):
        return "away"
    return "inactive"


def _version_counts() -> tuple[int, int]:
    """Return platform breaking and safe counts."""
    breaking = 0
    safe = 0
    for version in SchemaVersion.query.all():
        diff = version.diff_result or {}
        breaking += int(diff.get("breaking_count") or 0)
        safe += int(diff.get("safe_count") or 0)
    return breaking, safe


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def stats(current_user):
    """Return platform-wide admin statistics."""
    now = datetime.now(timezone.utc)
    breaking, safe = _version_counts()
    most_active = User.query.order_by(User.total_uploads.desc()).first()
    recent_users = User.query.order_by(User.created_at.desc()).limit(20).all()
    recent_users = sorted(
        recent_users,
        key=lambda user: user.last_active_at or user.created_at,
        reverse=True,
    )[:5]
    return jsonify(
        {
            "total_users": User.query.count(),
            "active_users_today": User.query.filter(User.last_active_at >= now - timedelta(days=1)).count(),
            "total_registries": APIRegistry.query.count(),
            "total_versions": SchemaVersion.query.count(),
            "total_breaking_changes": breaking,
            "total_safe_changes": safe,
            "new_users_this_week": User.query.filter(User.created_at >= now - timedelta(days=7)).count(),
            "most_active_user": {
                "email": most_active.email if most_active else None,
                "upload_count": most_active.total_uploads if most_active else 0,
            },
            "recent_users": [_user_row(user) for user in recent_users],
        }
    ), 200


@admin_bp.route("/users", methods=["GET"])
@admin_required
def users(current_user):
    """Return all users for admin management."""
    return jsonify({"users": [_user_row(user) for user in User.query.order_by(User.created_at.desc()).all()]}), 200


@admin_bp.route("/users/<user_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_user(user_id, current_user):
    """Suspend or reactivate a user."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        abort(400, description="Admin cannot suspend themselves")
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify(_user_row(user)), 200


@admin_bp.route("/users/<user_id>/make-admin", methods=["POST"])
@admin_required
def make_admin(user_id, current_user):
    """Promote a user to admin."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    user.is_admin = True
    db.session.commit()
    return jsonify(_user_row(user)), 200


@admin_bp.route("/registries", methods=["GET"])
@admin_required
def registries(current_user):
    """Return all registries across the platform."""
    return jsonify({"registries": [_registry_row(item) for item in APIRegistry.query.order_by(APIRegistry.created_at.desc()).all()]}), 200


@admin_bp.route("/registries/<registry_id>", methods=["GET"])
@admin_required
def registry_detail(registry_id, current_user):
    """Return full details for any registry."""
    registry = db.session.get(APIRegistry, registry_id)
    if not registry:
        abort(404)
    row = _registry_row(registry)
    row["description"] = registry.description
    row["versions"] = [
        {
            "id": version.id,
            "version": version.version,
            "status": version.status.value,
            "diff_result": version.diff_result,
            "uploaded_at": version.uploaded_at.isoformat(),
        }
        for version in registry.versions
    ]
    return jsonify(row), 200


def _user_row(user: User) -> dict:
    """Serialize a user with admin metadata."""
    return {
        "id": user.id,
        "email": user.email,
        "is_admin": bool(user.is_admin),
        "is_active": bool(user.is_active),
        "created_at": user.created_at.isoformat(),
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "last_active_at": user.last_active_at.isoformat() if user.last_active_at else None,
        "total_uploads": user.total_uploads or 0,
        "total_registries": APIRegistry.query.filter_by(owner_id=user.id).count(),
        "activity_status": _activity_status(user),
    }


def _registry_row(registry: APIRegistry) -> dict:
    """Serialize a registry for admin tables."""
    latest = registry.versions[0] if registry.versions else None
    breaking = sum(
        1 for version in registry.versions if (version.diff_result or {}).get("is_breaking")
    )
    return {
        "id": registry.id,
        "name": registry.name,
        "owner_email": registry.owner.email if registry.owner else "unknown",
        "created_at": registry.created_at.isoformat(),
        "version_count": len(registry.versions),
        "last_version_uploaded_at": latest.uploaded_at.isoformat() if latest else None,
        "breaking_changes_count": breaking,
    }
