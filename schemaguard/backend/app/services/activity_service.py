"""Activity logging service for registry and admin audit trails."""

import logging
from datetime import datetime, timezone

from app import db
from app.models.collaboration import ActivityAction, ActivityLog

logger = logging.getLogger(__name__)


def log_activity(
    registry_id: str | None,
    actor_email: str,
    actor_role: str,
    action: str,
    metadata: dict | None = None,
) -> None:
    """Persist an activity log entry without ever raising to callers."""
    try:
        entry = ActivityLog(
            registry_id=registry_id,
            actor_email=actor_email,
            actor_role=actor_role,
            action=ActivityAction(action),
            metadata_json=metadata or {},
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Failed to log activity")


def humanize_activity(entry: ActivityLog) -> str:
    """Build a readable activity sentence for a log entry."""
    actor = entry.actor_email
    meta = entry.metadata_json or {}
    action = entry.action.value if hasattr(entry.action, "value") else str(entry.action)
    descriptions = {
        "SCHEMA_UPLOADED": (
            f"{actor} uploaded version {meta.get('version', 'unknown')} - "
            f"{meta.get('breaking_count', 0)} breaking changes"
        ),
        "DIFF_VIEWED": (
            f"{actor} viewed diff {meta.get('from_version', 'previous')} -> "
            f"{meta.get('to_version', 'current')}"
        ),
        "MEMBER_ADDED": f"{actor} added {meta.get('member_email', 'a member')} as {meta.get('role', 'MEMBER')}",
        "MEMBER_REMOVED": f"{actor} removed {meta.get('member_email', 'a member')}",
        "SUBSCRIBER_ADDED": f"{actor} added subscriber {meta.get('subscriber_email', 'unknown')}",
        "SUBSCRIBER_REMOVED": f"{actor} removed subscriber {meta.get('subscriber_email', 'unknown')}",
        "MESSAGE_SENT": f"{actor} sent a message to Team B Lead",
        "REGISTRY_CREATED": f"{actor} created registry {meta.get('registry_name', 'unknown')}",
        "REGISTRY_DELETED": f"{actor} deleted registry {meta.get('registry_name', 'unknown')}",
        "ROLE_CHANGED": (
            f"{actor} changed {meta.get('member_email', 'a member')} to "
            f"{meta.get('role', 'MEMBER')}"
        ),
        "SUBSCRIBER_LEAD_CHANGED": (
            f"{actor} set {meta.get('subscriber_email', 'a subscriber')} as Team B Lead"
        ),
    }
    return descriptions.get(action, f"{actor} performed {action}")


def relative_time(value: datetime | None) -> str:
    """Return a compact relative timestamp."""
    if not value:
        return "never"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    seconds = max(0, int((datetime.now(timezone.utc) - value).total_seconds()))
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hours ago"
    days = hours // 24
    return f"{days} days ago"


def activity_response(entry: ActivityLog) -> dict:
    """Serialize an activity log entry for API responses."""
    return {
        "id": entry.id,
        "actor_email": entry.actor_email,
        "actor_role": entry.actor_role,
        "action": entry.action.value if hasattr(entry.action, "value") else str(entry.action),
        "metadata": entry.metadata_json or {},
        "created_at": entry.created_at.isoformat(),
        "relative_time": relative_time(entry.created_at),
        "human_readable_description": humanize_activity(entry),
    }
