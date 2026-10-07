"""Add title relations and franchise foundation.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "title_relations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_title_id", sa.Integer(), nullable=False),
        sa.Column("target_title_id", sa.Integer(), nullable=False),
        sa.Column("relation_type", sa.Enum(
            "ADAPTATION", "SEASON", "SEQUEL", "PREQUEL", "SPIN_OFF",
            "SIDE_STORY", "ALTERNATIVE", "RELATED", name="titlerelationtype"
        ), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.CheckConstraint("source_title_id != target_title_id", name="ck_title_relations_not_self"),
        sa.ForeignKeyConstraint(["source_title_id"], ["titles.id"]),
        sa.ForeignKeyConstraint(["target_title_id"], ["titles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_title_id", "target_title_id", "relation_type",
                            name="uq_title_relations_source_target_type"),
    )
    op.create_index("ix_title_relations_source_title_id", "title_relations", ["source_title_id"])
    op.create_index("ix_title_relations_target_title_id", "title_relations", ["target_title_id"])

    op.create_table(
        "franchises",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "franchise_titles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("franchise_id", sa.Integer(), nullable=False),
        sa.Column("title_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["franchise_id"], ["franchises.id"]),
        sa.ForeignKeyConstraint(["title_id"], ["titles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("franchise_id", "title_id", name="uq_franchise_titles_franchise_title"),
    )
    op.create_index("ix_franchise_titles_franchise_id", "franchise_titles", ["franchise_id"])
    op.create_index("ix_franchise_titles_title_id", "franchise_titles", ["title_id"])


def downgrade() -> None:
    op.drop_index("ix_franchise_titles_title_id", table_name="franchise_titles")
    op.drop_index("ix_franchise_titles_franchise_id", table_name="franchise_titles")
    op.drop_table("franchise_titles")
    op.drop_table("franchises")
    op.drop_index("ix_title_relations_target_title_id", table_name="title_relations")
    op.drop_index("ix_title_relations_source_title_id", table_name="title_relations")
    op.drop_table("title_relations")
