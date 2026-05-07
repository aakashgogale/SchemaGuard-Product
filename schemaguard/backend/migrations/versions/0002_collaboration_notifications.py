"""Add collaboration and notification fields.

Revision ID: 0002_collaboration_notifications
Revises: 0001_initial_schema
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import secrets


revision = "0002_collaboration_notifications"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create collaboration tables and add public/change fields."""
    op.add_column("api_registries", sa.Column("public_token", sa.String(length=96), nullable=True))
    connection = op.get_bind()
    registry_rows = connection.execute(sa.text("SELECT id FROM api_registries")).fetchall()
    for row in registry_rows:
        connection.execute(
            sa.text("UPDATE api_registries SET public_token = :token WHERE id = :id"),
            {"token": secrets.token_urlsafe(32), "id": row[0]},
        )
    op.alter_column("api_registries", "public_token", nullable=False)
    op.create_unique_constraint("uq_api_registries_public_token", "api_registries", ["public_token"])
    op.add_column("schema_versions", sa.Column("change_reason", sa.String(length=500), nullable=True))

    op.create_table(
        "api_members",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("registry_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("added_by", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("added_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["added_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["registry_id"], ["api_registries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registry_id", "email", name="uq_registry_member_email"),
    )
    op.create_index("ix_api_members_registry_id", "api_members", ["registry_id"])

    op.create_table(
        "api_subscribers",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("registry_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("notify_breaking_only", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("subscribed_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["registry_id"], ["api_registries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registry_id", "email", name="uq_registry_subscriber_email"),
    )
    op.create_index("ix_api_subscribers_registry_id", "api_subscribers", ["registry_id"])


def downgrade() -> None:
    """Drop collaboration tables and public/change fields."""
    op.drop_index("ix_api_subscribers_registry_id", table_name="api_subscribers")
    op.drop_table("api_subscribers")
    op.drop_index("ix_api_members_registry_id", table_name="api_members")
    op.drop_table("api_members")
    op.drop_column("schema_versions", "change_reason")
    op.drop_constraint("uq_api_registries_public_token", "api_registries", type_="unique")
    op.drop_column("api_registries", "public_token")
