"""Add library entry statuses.

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.Enum(
                    "watching",
                    "reading",
                    "completed",
                    "planned",
                    "paused",
                    "dropped",
                    name="librarystatus",
            ),
                nullable=False,
                server_default="planned",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.drop_column("status")
