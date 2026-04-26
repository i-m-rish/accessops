"""add provisioning lifecycle fields

Revision ID: 9f4c2b1a7d21
Revises: 7bb5211c522b
Create Date: 2026-04-26 05:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f4c2b1a7d21"
down_revision: Union[str, None] = "7bb5211c522b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    provisioning_status = sa.Enum(
        "NOT_STARTED",
        "QUEUED",
        "PROVISIONED",
        "FAILED",
        name="provisioning_status",
    )
    provisioning_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "access_requests",
        sa.Column(
            "provisioning_status",
            provisioning_status,
            server_default="NOT_STARTED",
            nullable=False,
        ),
    )
    op.add_column("access_requests", sa.Column("provisioned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("access_requests", sa.Column("provisioning_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("access_requests", "provisioning_error")
    op.drop_column("access_requests", "provisioned_at")
    op.drop_column("access_requests", "provisioning_status")

    provisioning_status = sa.Enum(
        "NOT_STARTED",
        "QUEUED",
        "PROVISIONED",
        "FAILED",
        name="provisioning_status",
    )
    provisioning_status.drop(op.get_bind(), checkfirst=True)
