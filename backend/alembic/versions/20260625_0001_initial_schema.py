"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-25

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


project_status_enum = postgresql.ENUM(
    "active",
    "completed",
    "on_hold",
    "attention",
    name="project_status",
    create_type=False,
)
act_status_enum = postgresql.ENUM(
    "not_sent",
    "waiting_signature",
    "closed",
    "attention",
    name="act_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    project_status_enum.create(bind, checkfirst=True)
    act_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("inn", sa.String(20), nullable=False),
        sa.Column("ogrn", sa.String(20), nullable=True),
        sa.Column("bank_account", sa.String(30), nullable=True),
        sa.Column("contact_person", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("inn", name="uq_clients_inn"),
    )
    op.create_index("ix_clients_inn", "clients", ["inn"])

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", project_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_projects_client_id", "projects", ["client_id"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("payment_date", sa.Date, nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_purpose", sa.String(1000), nullable=False),
        sa.Column("service_type", sa.String(64), nullable=False),
        sa.Column("invoice_number", sa.String(128), nullable=True),
        sa.Column("contract_number", sa.String(128), nullable=True),
        sa.Column("doc_number", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_payments_project_id", "payments", ["project_id"])
    op.create_index("ix_payments_client_id", "payments", ["client_id"])
    op.create_index("ix_payments_payment_date", "payments", ["payment_date"])
    op.create_index("ix_payments_service_type", "payments", ["service_type"])

    op.create_table(
        "acts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "payment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_sent", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_signed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", act_status_enum, nullable=False, server_default="not_sent"),
        sa.Column("manager_comment", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("payment_id", name="uq_acts_payment_id"),
    )
    op.create_index("ix_acts_status", "acts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_acts_status", table_name="acts")
    op.drop_table("acts")
    op.drop_index("ix_payments_service_type", table_name="payments")
    op.drop_index("ix_payments_payment_date", table_name="payments")
    op.drop_index("ix_payments_client_id", table_name="payments")
    op.drop_index("ix_payments_project_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_projects_client_id", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_clients_inn", table_name="clients")
    op.drop_table("clients")

    bind = op.get_bind()
    act_status_enum.drop(bind, checkfirst=True)
    project_status_enum.drop(bind, checkfirst=True)
