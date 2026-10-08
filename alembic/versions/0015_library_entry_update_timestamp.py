"""Add library entry update timestamp.

Revision ID: 0015
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.alter_column("updated_at", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.drop_column("updated_at")
