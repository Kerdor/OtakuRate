"""Replace library statuses with user lists and tags.

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


ANIME_LISTS = (
    ("watching", "Смотрю"),
    ("completed", "Просмотрено"),
    ("planned", "Запланировано"),
    ("paused", "Отложено"),
    ("dropped", "Брошено"),
)

MANGA_LISTS = (
    ("reading", "Читаю"),
    ("completed", "Прочитано"),
    ("planned", "Запланировано"),
    ("paused", "Отложено"),
    ("dropped", "Брошено"),
)


def upgrade() -> None:
    op.create_table(
        "user_lists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("system_key", sa.String(length=64), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "media_type", "name",
            name="uq_user_lists_user_media_name",
        ),
        sa.UniqueConstraint(
            "user_id", "media_type", "system_key",
            name="uq_user_lists_user_media_system_key",
        ),
    )

    op.create_table(
        "user_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "name",
            name="uq_user_tags_user_name",
        ),
    )

    op.create_table(
        "library_entry_tags",
        sa.Column("library_entry_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["library_entry_id"], ["library_entries.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["user_tags.id"]),
        sa.PrimaryKeyConstraint("library_entry_id", "tag_id"),
        sa.UniqueConstraint(
            "library_entry_id", "tag_id",
            name="uq_library_entry_tags_entry_tag",
        ),
    )

    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.add_column(sa.Column("list_id", sa.Integer(), nullable=True))

    connection = op.get_bind()

    user_rows = connection.execute(
        sa.text("SELECT id FROM users ORDER BY id")
    ).fetchall()

    for (user_id,) in user_rows:
        for system_key, name in ANIME_LISTS:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO user_lists
                        (user_id, media_type, name, system_key, is_system, created_at)
                    VALUES
                        (:user_id, 'anime', :name, :system_key, 1, CURRENT_TIMESTAMP)
                    """
                ),
                {"user_id": user_id, "name": name, "system_key": system_key},
            )
        for system_key, name in MANGA_LISTS:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO user_lists
                        (user_id, media_type, name, system_key, is_system, created_at)
                    VALUES
                        (:user_id, 'manga', :name, :system_key, 1, CURRENT_TIMESTAMP)
                    """
                ),
                {"user_id": user_id, "name": name, "system_key": system_key},
            )

    connection.execute(
        sa.text(
            """
            UPDATE library_entries
            SET list_id = (
                SELECT ul.id
                FROM user_lists AS ul
                JOIN titles AS t ON t.id = library_entries.title_id
                WHERE ul.user_id = library_entries.user_id
                  AND ul.media_type = t.media_type
                  AND ul.system_key = library_entries.status
            )
            """
        )
    )

    missing = connection.execute(
        sa.text("SELECT COUNT(*) FROM library_entries WHERE list_id IS NULL")
    ).scalar_one()
    if missing:
        raise RuntimeError(
            f"Could not map {missing} library entries to a user list."
        )

    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.alter_column("list_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_library_entries_list_id",
            "user_lists",
            ["list_id"],
            ["id"],
        )
        batch_op.drop_column("status")


def downgrade() -> None:
    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=16),
                nullable=True,
            )
        )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE library_entries
            SET status = (
                SELECT ul.system_key
                FROM user_lists AS ul
                WHERE ul.id = library_entries.list_id
            )
            """
        )
    )

    with op.batch_alter_table("library_entries") as batch_op:
        batch_op.alter_column("status", nullable=False)
        batch_op.drop_constraint(
            "fk_library_entries_list_id",
            type_="foreignkey",
        )
        batch_op.drop_column("list_id")

    op.drop_table("library_entry_tags")
    op.drop_table("user_tags")
    op.drop_table("user_lists")
