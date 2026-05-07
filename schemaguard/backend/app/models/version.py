"""Schema Version database model."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app import db


class VersionStatus(enum.Enum):
    """Allowed statuses for a schema version."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


class SchemaVersion(db.Model):
    """Represents a specific version of an API schema."""

    __tablename__ = "schema_versions"
    __table_args__ = (
        db.UniqueConstraint("registry_id", "version", name="uq_registry_version"),
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
    uploaded_by_id = db.Column(
        UUID(as_uuid=False).with_variant(db.String(36), "sqlite"),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version = db.Column(db.String(50), nullable=False)
    schema_json = db.Column(JSONB().with_variant(db.JSON, "sqlite"), nullable=False)
    change_reason = db.Column(db.String(500), nullable=True)
    status = db.Column(
        db.Enum(VersionStatus),
        nullable=False,
        default=VersionStatus.PENDING,
    )
    diff_result = db.Column(JSONB().with_variant(db.JSON, "sqlite"), nullable=True)
    uploaded_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    registry = db.relationship("APIRegistry", back_populates="versions")
    uploaded_by = db.relationship("User")

    def __repr__(self) -> str:
        """Return a readable debug representation."""
        return f"<SchemaVersion {self.version} ({self.status.value})>"
