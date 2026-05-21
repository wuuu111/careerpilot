"""company profiles for phase 3

Revision ID: 20260521_000003
Revises: 20260521_000002
Create Date: 2026-05-21 00:00:03
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260521_000003"
down_revision = "20260521_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("application_id", sa.String(length=36), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_text", sa.Text(), nullable=False),
        sa.Column("embedding_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("application_id", name="uq_company_profiles_application_id"),
    )
    op.create_index("ix_company_profiles_application_id", "company_profiles", ["application_id"], unique=True)
    op.create_index("ix_company_profiles_user_id", "company_profiles", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_company_profiles_user_id", table_name="company_profiles")
    op.drop_index("ix_company_profiles_application_id", table_name="company_profiles")
    op.drop_table("company_profiles")
