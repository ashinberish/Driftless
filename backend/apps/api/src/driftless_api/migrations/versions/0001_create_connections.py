"""create connections

Revision ID: 0001
Revises:
Create Date: 2026-11-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "connections",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("engine", sa.String(32), nullable=False),
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("database", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("secret_ref", sa.String(512), nullable=False),
        sa.Column("ssl_mode", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_connections"),
        sa.UniqueConstraint("name", name="uq_connections_name"),
    )
    op.create_index("ix_connections_engine", "connections", ["engine"])


def downgrade() -> None:
    op.drop_index("ix_connections_engine", table_name="connections")
    op.drop_table("connections")
