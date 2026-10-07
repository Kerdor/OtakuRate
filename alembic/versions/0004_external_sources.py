"""Add external source and title relations.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("base_url", sa.String(length=1024), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_external_sources_key", "external_sources", ["key"], unique=False)

    op.create_table(
        "external_titles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("media_type", sa.Enum("ANIME", "MANGA", name="mediatype"), nullable=True),
        sa.Column("external_title", sa.String(length=255), nullable=True),
        sa.Column("alternative_titles", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["external_sources.id"]),
        sa.ForeignKeyConstraint(["title_id"], ["titles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_external_titles_source_external_id"),
    )
    op.create_index(
        "ix_external_titles_source_external_id",
        "external_titles",
        ["source_id", "external_id"],
        unique=False,
    )

    op.create_table(
        "user_external_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_user_id", sa.String(length=255), nullable=True),
        sa.Column("external_username", sa.String(length=255), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["external_sources.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source_id", name="uq_user_external_accounts_user_source"),
    )


def downgrade() -> None:
    op.drop_table("user_external_accounts")
    op.drop_index("ix_external_titles_source_external_id", table_name="external_titles")
    op.drop_table("external_titles")
    op.drop_index("ix_external_sources_key", table_name="external_sources")
    op.drop_table("external_sources")
