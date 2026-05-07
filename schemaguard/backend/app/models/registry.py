"""API Registry database model."""

import uuid
import secrets
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app import db


class APIRegistry(db.Model):
    """Represents a registered API whose schemas are tracked."""

    __tablename__ = "api_registries"
    __table_args__ = (
        db.UniqueConstraint("owner_id", "name", name="uq_owner_api_name"),
    )

    id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    owner_id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    public_token = db.Column(
        db.String(96),
        unique=True,
        nullable=False,
        default=lambda: secrets.token_urlsafe(32),
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    owner = db.relationship("User", back_populates="registries")
    versions = db.relationship(
        "SchemaVersion",
        back_populates="registry",
        cascade="all, delete-orphan",
        order_by="SchemaVersion.uploaded_at.desc()",
    )
    members = db.relationship(
        "APIMember",
        back_populates="registry",
        cascade="all, delete-orphan",
        order_by="APIMember.added_at.desc()",
    )
    subscribers = db.relationship(
        "APISubscriber",
        back_populates="registry",
        cascade="all, delete-orphan",
        order_by="APISubscriber.subscribed_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<APIRegistry {self.name}>"
