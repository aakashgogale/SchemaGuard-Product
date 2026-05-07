"""Initial SchemaGuard schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _uuid_type():
    """Return the UUID column type used by PostgreSQL migrations."""
    return postgresql.UUID(as_uuid=False)


def upgrade() -> None:
    """Create users, API registries, and schema versions."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    version_status = postgresql.ENUM(
        "PENDING",
        "ACTIVE",
        "DEPRECATED",
        name="versionstatus",
        create_type=False,
    )
    version_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", _uuid_type(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "api_registries",
        sa.Column("id", _uuid_type(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_id", _uuid_type(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_owner_api_name"),
    )
    op.create_index("ix_api_registries_owner_id", "api_registries", ["owner_id"])

    op.create_table(
        "schema_versions",
        sa.Column("id", _uuid_type(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("registry_id", _uuid_type(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("schema_json", postgresql.JSONB(), nullable=False),
        sa.Column("status", version_status, server_default="PENDING", nullable=False),
        sa.Column("diff_result", postgresql.JSONB(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["registry_id"], ["api_registries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registry_id", "version", name="uq_registry_version"),
    )
    op.create_index("ix_schema_versions_registry_id", "schema_versions", ["registry_id"])


def downgrade() -> None:
    """Drop SchemaGuard tables and enum."""
    op.drop_index("ix_schema_versions_registry_id", table_name="schema_versions")
    op.drop_table("schema_versions")
    op.drop_index("ix_api_registries_owner_id", table_name="api_registries")
    op.drop_table("api_registries")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    postgresql.ENUM(name="versionstatus").drop(op.get_bind(), checkfirst=True)
