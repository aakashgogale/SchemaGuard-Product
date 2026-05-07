"""Collaboration models for API teams and subscribers."""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app import db


class MemberRole(enum.Enum):
    """Roles available to invited Team A members."""

    CO_LEAD = "CO_LEAD"
    MEMBER = "MEMBER"


class SenderType(enum.Enum):
    """Message sender groups."""

    TEAM_A = "TEAM_A"
    TEAM_B = "TEAM_B"


class ActivityAction(enum.Enum):
    """Tracked registry activity actions."""

    SCHEMA_UPLOADED = "SCHEMA_UPLOADED"
    DIFF_VIEWED = "DIFF_VIEWED"
    MEMBER_ADDED = "MEMBER_ADDED"
    MEMBER_REMOVED = "MEMBER_REMOVED"
    SUBSCRIBER_ADDED = "SUBSCRIBER_ADDED"
    SUBSCRIBER_REMOVED = "SUBSCRIBER_REMOVED"
    MESSAGE_SENT = "MESSAGE_SENT"
    REGISTRY_CREATED = "REGISTRY_CREATED"
    REGISTRY_DELETED = "REGISTRY_DELETED"
    ROLE_CHANGED = "ROLE_CHANGED"
    SUBSCRIBER_LEAD_CHANGED = "SUBSCRIBER_LEAD_CHANGED"


class APIMember(db.Model):
    """Represents a Team A member notified for every API change."""

    __tablename__ = "api_members"
    __table_args__ = (
        db.UniqueConstraint("registry_id", "email", name="uq_registry_member_email"),
    )

    id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    registry_id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        db.ForeignKey("api_registries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(MemberRole),
        nullable=False,
        default=MemberRole.MEMBER,
    )
    added_by = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    added_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    registry = db.relationship("APIRegistry", back_populates="members")
    added_by_user = db.relationship("User")


class APISubscriber(db.Model):
    """Represents a Team B subscriber notified about API changes."""

    __tablename__ = "api_subscribers"
    __table_args__ = (
        db.UniqueConstraint("registry_id", "email", name="uq_registry_subscriber_email"),
    )

    id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    registry_id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        db.ForeignKey("api_registries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = db.Column(db.String(255), nullable=False)
    team_name = db.Column(db.String(100), nullable=True)
    is_lead = db.Column(db.Boolean, nullable=False, default=False)
    webhook_url = db.Column(db.String(500), nullable=True)
    notify_breaking_only = db.Column(db.Boolean, nullable=False, default=True)
    subscribed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    registry = db.relationship("APIRegistry", back_populates="subscribers")


class RegistryMessage(db.Model):
    """A simple message thread entry between Team A and Team B lead."""

    __tablename__ = "registry_messages"

    id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    registry_id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        db.ForeignKey("api_registries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type = db.Column(db.Enum(SenderType), nullable=False)
    sender_email = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_read = db.Column(db.Boolean, nullable=False, default=False)

    registry = db.relationship("APIRegistry", backref=db.backref("messages", cascade="all, delete-orphan"))


class ActivityLog(db.Model):
    """Audit activity entry for registry and platform events."""

    __tablename__ = "activity_logs"

    id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    registry_id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        db.ForeignKey("api_registries.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    actor_email = db.Column(db.String(255), nullable=False)
    actor_role = db.Column(db.String(50), nullable=False)
    action = db.Column(db.Enum(ActivityAction), nullable=False)
    metadata_json = db.Column("metadata", JSONB().with_variant(db.JSON, "sqlite"), nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    registry = db.relationship("APIRegistry", backref=db.backref("activity_logs", cascade="all, delete-orphan"))
