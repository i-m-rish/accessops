"""access_requests: cascade requester fk

Revision ID: c6900fef97a6
Revises: a97fc442ad66
Create Date: 2026-01-06 04:26:51.233423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c6900fef97a6"
down_revision: Union[str, None] = "a97fc442ad66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite-safe strategy: rebuild table using create/copy/drop/rename.
    op.create_table(
        "access_requests__tmp",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("requester_id", sa.String(36), nullable=False),
        sa.Column("resource", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "APPROVED", "REJECTED", name="request_status"), nullable=False),
        sa.Column("decided_by", sa.String(36), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Copy data (column order must match)
    op.execute(
        """
        INSERT INTO access_requests__tmp
        (id, requester_id, resource, action, justification, status, decided_by, decided_at, created_at)
        SELECT
        id, requester_id, resource, action, justification, status, decided_by, decided_at, created_at
        FROM access_requests
        """
    )

    op.drop_table("access_requests")
    op.rename_table("access_requests__tmp", "access_requests")


def downgrade() -> None:
    # Rebuild back without ondelete behaviors (SQLite-safe).
    op.create_table(
        "access_requests__tmp",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("requester_id", sa.String(36), nullable=False),
        sa.Column("resource", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "APPROVED", "REJECTED", name="request_status"), nullable=False),
        sa.Column("decided_by", sa.String(36), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        """
        INSERT INTO access_requests__tmp
        (id, requester_id, resource, action, justification, status, decided_by, decided_at, created_at)
        SELECT
        id, requester_id, resource, action, justification, status, decided_by, decided_at, created_at
        FROM access_requests
        """
    )

    op.drop_table("access_requests")
    op.rename_table("access_requests__tmp", "access_requests")
