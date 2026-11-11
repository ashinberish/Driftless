"""create migrations and assessments

Revision ID: 0002
Revises: 0001
Create Date: 2026-12-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_DOC = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "migrations",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("source_connection_id", sa.String(40), nullable=False),
        sa.Column("source_engine", sa.String(32), nullable=False),
        sa.Column("target_engine", sa.String(32), nullable=False),
        sa.Column("target_connection_id", sa.String(40), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_connection_id"],
            ["connections.id"],
            name="fk_migrations_source_connection_id_connections",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_connection_id"],
            ["connections.id"],
            name="fk_migrations_target_connection_id_connections",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_migrations"),
        sa.UniqueConstraint("name", name="uq_migrations_name"),
    )
    op.create_index("ix_migrations_source_connection_id", "migrations", ["source_connection_id"])
    op.create_index("ix_migrations_target_connection_id", "migrations", ["target_connection_id"])
    op.create_index("ix_migrations_status", "migrations", ["status"])

    op.create_table(
        "assessments",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("migration_id", sa.String(40), nullable=False),
        sa.Column("result", JSON_DOC, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["migration_id"],
            ["migrations.id"],
            name="fk_assessments_migration_id_migrations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_assessments"),
    )
    op.create_index(
        "ix_assessments_migration_created", "assessments", ["migration_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_assessments_migration_created", table_name="assessments")
    op.drop_table("assessments")
    op.drop_index("ix_migrations_status", table_name="migrations")
    op.drop_index("ix_migrations_target_connection_id", table_name="migrations")
    op.drop_index("ix_migrations_source_connection_id", table_name="migrations")
    op.drop_table("migrations")
