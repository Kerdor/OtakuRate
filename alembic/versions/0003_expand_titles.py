"""Expand the titles table.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("titles") as batch_op:
        batch_op.add_column(
            sa.Column("alternative_titles", sa.JSON(), nullable=False)
        )
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("cover_url", sa.String(length=1024), nullable=True)
        )
        batch_op.add_column(sa.Column("release_date", sa.Date(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "release_status",
                sa.Enum(
                    "UPCOMING",
                    "ONGOING",
                    "FINISHED",
                    "HIATUS",
                    "CANCELLED",
                    name="releasestatus",
                ),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("genres", sa.JSON(), nullable=False))
        batch_op.add_column(sa.Column("tags", sa.JSON(), nullable=False))
        batch_op.add_column(sa.Column("metadata", sa.JSON(), nullable=False))
        batch_op.drop_column("external_ids")


def downgrade() -> None:
    with op.batch_alter_table("titles") as batch_op:
        batch_op.add_column(sa.Column("external_ids", sa.JSON(), nullable=False))
        batch_op.drop_column("metadata")
        batch_op.drop_column("tags")
        batch_op.drop_column("genres")
        batch_op.drop_column("release_status")
        batch_op.drop_column("release_date")
        batch_op.drop_column("cover_url")
        batch_op.drop_column("description")
        batch_op.drop_column("alternative_titles")
