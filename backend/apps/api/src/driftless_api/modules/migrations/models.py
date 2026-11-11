"""ORM mapping for migrations and their assessment runs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from driftless_api.platform.db import Base, UtcDateTime

JsonDocument = JSON().with_variant(JSONB(), "postgresql")


class MigrationRecord(Base):
    __tablename__ = "migrations"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    source_connection_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("connections.id", ondelete="RESTRICT"), index=True
    )
    source_engine: Mapped[str] = mapped_column(String(32))
    target_engine: Mapped[str] = mapped_column(String(32))
    target_connection_id: Mapped[str | None] = mapped_column(
        String(40), ForeignKey("connections.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime())
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime())


class AssessmentRecord(Base):
    __tablename__ = "assessments"
    __table_args__ = (Index("ix_assessments_migration_created", "migration_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    migration_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("migrations.id", ondelete="CASCADE")
    )
    result: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime())
