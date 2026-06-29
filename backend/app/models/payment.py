from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.act import Act
    from app.models.client import Client
    from app.models.project import Project


class Payment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "payments"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_purpose: Mapped[str] = mapped_column(String(1000), nullable=False)
    service_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    invoice_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    contract_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    doc_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    project: Mapped[Project] = relationship(back_populates="payments")
    client: Mapped[Client] = relationship(back_populates="payments")
    act: Mapped[Act | None] = relationship(
        back_populates="payment",
        uselist=False,
        cascade="all, delete-orphan",
    )
