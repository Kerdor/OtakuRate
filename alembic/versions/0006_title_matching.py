"""Add title matching candidates.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "title_match_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("candidate_title_id", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "CONFIRMED", "REJECTED", name="matchstatus"), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["external_sources.id"]),
        sa.ForeignKeyConstraint(["candidate_title_id"], ["titles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "external_id", "candidate_title_id", name="uq_title_match_candidates_source_external_title"),
    )
    op.create_index("ix_title_match_candidates_source_external_id", "title_match_candidates", ["source_id", "external_id"])


def downgrade() -> None:
    op.drop_index("ix_title_match_candidates_source_external_id", table_name="title_match_candidates")
    op.drop_table("title_match_candidates")
