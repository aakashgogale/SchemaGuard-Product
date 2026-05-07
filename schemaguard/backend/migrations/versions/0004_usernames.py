"""Add user display usernames.

Revision ID: 0004_usernames
Revises: 0003_admin_roles_activity
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_usernames"
down_revision = "0003_admin_roles_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add username column and backfill existing users."""
    op.add_column("users", sa.Column("username", sa.String(length=100), nullable=True))
    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id, email FROM users")).fetchall()
    for user_id, email in users:
        connection.execute(
            sa.text("UPDATE users SET username = :username WHERE id = :id"),
            {"username": email.split("@")[0], "id": user_id},
        )


def downgrade() -> None:
    """Remove username column."""
    op.drop_column("users", "username")
