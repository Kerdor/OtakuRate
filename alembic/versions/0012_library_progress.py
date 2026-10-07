"""Add generic library progress.

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.add_column(sa.Column("progress_current", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("progress_total", sa.Integer(), nullable=True))
        batch_op.create_check_constraint(
            "ck_library_entries_progress_current_nonnegative",
            "progress_current IS NULL OR progress_current >= 0",
        )
        batch_op.create_check_constraint(
            "ck_library_entries_progress_total_positive",
            "progress_total IS NULL OR progress_total > 0",
        )
        batch_op.create_check_constraint(
            "ck_library_entries_progress_not_over_total",
            "progress_current IS NULL OR progress_total IS NULL OR progress_current <= progress_total",
        )


def downgrade() -> None:
    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.drop_constraint(
            "ck_library_entries_progress_not_over_total",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_library_entries_progress_total_positive",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_library_entries_progress_current_nonnegative",
            type_="check",
        )
        batch_op.drop_column("progress_total")
        batch_op.drop_column("progress_current")
