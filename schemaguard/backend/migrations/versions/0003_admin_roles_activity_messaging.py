"""Add admin, roles, activity, and messaging.

Revision ID: 0003_admin_roles_activity
Revises: 0002_collaboration_notifications
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_admin_roles_activity"
down_revision = "0002_collaboration_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply admin, roles, activity, and messaging schema."""
    member_role = postgresql.ENUM(
        "CO_LEAD",
        "MEMBER",
        name="memberrole",
        create_type=False,
    )
    sender_type = postgresql.ENUM(
        "TEAM_A",
        "TEAM_B",
        name="sendertype",
        create_type=False,
    )
    activity_action = postgresql.ENUM(
        "SCHEMA_UPLOADED",
        "DIFF_VIEWED",
        "MEMBER_ADDED",
        "MEMBER_REMOVED",
        "SUBSCRIBER_ADDED",
        "SUBSCRIBER_REMOVED",
        "MESSAGE_SENT",
        "REGISTRY_CREATED",
        "REGISTRY_DELETED",
        "ROLE_CHANGED",
        "SUBSCRIBER_LEAD_CHANGED",
        name="activityaction",
        create_type=False,
    )
    bind = op.get_bind()
    member_role.create(bind, checkfirst=True)
    sender_type.create(bind, checkfirst=True)
    activity_action.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("last_active_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("users", sa.Column("total_uploads", sa.Integer(), server_default="0", nullable=False))
    connection = op.get_bind()
    first_user = connection.execute(
        sa.text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
    ).fetchone()
    if first_user:
        connection.execute(sa.text("UPDATE users SET is_admin = true WHERE id = :id"), {"id": first_user[0]})

    op.add_column("schema_versions", sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=False), nullable=True))
    op.create_foreign_key("fk_schema_versions_uploaded_by", "schema_versions", "users", ["uploaded_by_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_schema_versions_uploaded_by_id", "schema_versions", ["uploaded_by_id"])

    op.add_column("api_members", sa.Column("role", member_role, server_default="MEMBER", nullable=False))
    op.add_column("api_subscribers", sa.Column("team_name", sa.String(length=100), nullable=True))
    op.add_column("api_subscribers", sa.Column("is_lead", sa.Boolean(), server_default=sa.text("false"), nullable=False))

    op.create_table(
        "registry_messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("registry_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("sender_type", sender_type, nullable=False),
        sa.Column("sender_email", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["registry_id"], ["api_registries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registry_messages_registry_id", "registry_messages", ["registry_id"])

    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("registry_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=False),
        sa.Column("actor_role", sa.String(length=50), nullable=False),
        sa.Column(
            "action",
            activity_action,
            nullable=False,
        ),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["registry_id"], ["api_registries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_logs_registry_id", "activity_logs", ["registry_id"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])


def downgrade() -> None:
    """Revert admin, roles, activity, and messaging schema."""
    op.drop_index("ix_activity_logs_created_at", table_name="activity_logs")
    op.drop_index("ix_activity_logs_registry_id", table_name="activity_logs")
    op.drop_table("activity_logs")
    op.drop_index("ix_registry_messages_registry_id", table_name="registry_messages")
    op.drop_table("registry_messages")
    op.drop_column("api_subscribers", "is_lead")
    op.drop_column("api_subscribers", "team_name")
    op.drop_column("api_members", "role")
    op.drop_index("ix_schema_versions_uploaded_by_id", table_name="schema_versions")
    op.drop_constraint("fk_schema_versions_uploaded_by", "schema_versions", type_="foreignkey")
    op.drop_column("schema_versions", "uploaded_by_id")
    op.drop_column("users", "total_uploads")
    op.drop_column("users", "is_active")
    op.drop_column("users", "last_active_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "is_admin")
    postgresql.ENUM(name="activityaction").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="sendertype").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="memberrole").drop(op.get_bind(), checkfirst=True)
