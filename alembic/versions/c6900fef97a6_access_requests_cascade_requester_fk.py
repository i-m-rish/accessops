"""access_requests: cascade requester fk

Revision ID: c6900fef97a6
Revises: a97fc442ad66
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "c6900fef97a6"
down_revision = "a97fc442ad66"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite constraints created in the previous migration may be unnamed or
    # auto-named, so dropping by a hardcoded name is not reliable.
    # Force a table recreation and define the correct FKs explicitly.
    with op.batch_alter_table("access_requests", recreate="always") as batch_op:
        # Recreate desired foreign keys with explicit names + ON DELETE behavior
        batch_op.create_foreign_key(
            "fk_access_requests_requester_id_users",
            "users",
            ["requester_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_access_requests_decided_by_users",
            "users",
            ["decided_by"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    # Recreate original behavior (no explicit ON DELETE)
    with op.batch_alter_table("access_requests", recreate="always") as batch_op:
        batch_op.create_foreign_key(
            "fk_access_requests_requester_id_users",
            "users",
            ["requester_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_access_requests_decided_by_users",
            "users",
            ["decided_by"],
            ["id"],
        )
