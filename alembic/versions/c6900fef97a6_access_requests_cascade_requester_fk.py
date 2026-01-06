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
    # Drop existing FK constraints (names depend on how they were created)
    op.drop_constraint("access_requests_decided_by_fkey", "access_requests", type_="foreignkey")
    op.drop_constraint("access_requests_requester_id_fkey", "access_requests", type_="foreignkey")

    # Recreate with desired ON DELETE behavior
    op.create_foreign_key(
        "access_requests_requester_id_fkey",
        "access_requests",
        "users",
        ["requester_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "access_requests_decided_by_fkey",
        "access_requests",
        "users",
        ["decided_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("access_requests_decided_by_fkey", "access_requests", type_="foreignkey")
    op.drop_constraint("access_requests_requester_id_fkey", "access_requests", type_="foreignkey")

    op.create_foreign_key(
        "access_requests_requester_id_fkey",
        "access_requests",
        "users",
        ["requester_id"],
        ["id"],
    )
    op.create_foreign_key(
        "access_requests_decided_by_fkey",
        "access_requests",
        "users",
        ["decided_by"],
        ["id"],
    )
