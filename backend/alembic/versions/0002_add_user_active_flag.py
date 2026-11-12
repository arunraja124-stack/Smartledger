"""Add user activation flag.

Revision ID: 0002_add_user_active_flag
Revises: 0001_initial_schema
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_user_active_flag"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("users", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "is_active")
