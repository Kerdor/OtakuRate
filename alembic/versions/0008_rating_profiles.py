"""Add rating profiles and criterion weights.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


ANIME_KEYS = [
    "story", "characters", "emotions", "interest", "atmosphere",
    "world", "development", "visuals", "sound", "aftertaste",
]
MANGA_KEYS = [
    "story", "characters", "emotions", "interest", "atmosphere",
    "world", "development", "drawing", "paneling", "aftertaste",
]
CRITERION_NAMES = {
    "story": "Сюжет",
    "characters": "Персонажи",
    "emotions": "Эмоции",
    "interest": "Интерес",
    "atmosphere": "Атмосфера",
    "world": "Мир",
    "development": "Развитие",
    "visuals": "Визуал",
    "sound": "Звук",
    "drawing": "Рисовка",
    "paneling": "Подача/панели",
    "aftertaste": "Послевкусие",
}


def upgrade() -> None:
    op.create_table(
        "rating_criteria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "rating_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("media_type", sa.Enum("anime", "manga", name="ratingprofilemediatype"), nullable=False),
        sa.Column("profile_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "media_type", "profile_key", "version", name="uq_rating_profiles_user_media_key_version"),
    )
    op.create_table(
        "rating_profile_criteria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("criterion_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.CheckConstraint("weight > 0", name="ck_rating_profile_criteria_weight_positive"),
        sa.CheckConstraint("order_index >= 0", name="ck_rating_profile_criteria_order_nonnegative"),
        sa.ForeignKeyConstraint(["profile_id"], ["rating_profiles.id"]),
        sa.ForeignKeyConstraint(["criterion_id"], ["rating_criteria.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "criterion_id", name="uq_rating_profile_criteria_profile_criterion"),
        sa.UniqueConstraint("profile_id", "order_index", name="uq_rating_profile_criteria_profile_order"),
    )

    for key, name in CRITERION_NAMES.items():
        op.execute(sa.text("INSERT INTO rating_criteria (key, name) VALUES (:key, :name)").bindparams(key=key, name=name))

    bind = op.get_bind()
    criterion_ids = {
        row.key: row.id for row in bind.execute(sa.text("SELECT id, key FROM rating_criteria")).mappings()
    }
    for media_type, keys in (("anime", ANIME_KEYS), ("manga", MANGA_KEYS)):
        bind.execute(sa.text("INSERT INTO rating_profiles (user_id, media_type, profile_key, name, version, is_default) VALUES (NULL, :media_type, :profile_key, :name, 1, 1)").bindparams(media_type=media_type, profile_key="standard", name="Стандартный"))
        profile_id = bind.execute(sa.text("SELECT id FROM rating_profiles WHERE user_id IS NULL AND media_type = :media_type AND profile_key = :profile_key AND version = 1").bindparams(media_type=media_type, profile_key="standard")).scalar_one()
        for order_index, key in enumerate(keys):
            bind.execute(sa.text("INSERT INTO rating_profile_criteria (profile_id, criterion_id, weight, order_index, enabled) VALUES (:profile_id, :criterion_id, 1.0, :order_index, 1)").bindparams(profile_id=profile_id, criterion_id=criterion_ids[key], order_index=order_index))

    with op.batch_alter_table("user_ratings") as batch_op:
        batch_op.add_column(sa.Column("rating_profile_version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    with op.batch_alter_table("user_ratings") as batch_op:
        batch_op.drop_column("rating_profile_version")
    op.drop_table("rating_profile_criteria")
    op.drop_table("rating_profiles")
    op.drop_table("rating_criteria")
    sa.Enum(name="ratingprofilemediatype").drop(op.get_bind(), checkfirst=True)