"""SQLAlchemy ORM models.

ORM types are confined to the infrastructure layer and never leak into
domain or application.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.engine import Base


class PantryItemModel(Base):
    """Persistence representation of a pantry item."""

    __tablename__ = "pantry_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
