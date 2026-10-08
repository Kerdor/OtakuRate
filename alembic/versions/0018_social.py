"""Add friend requests for social features."""

import sqlalchemy as sa
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "friend_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("addressee_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "rejected", name="friendrequeststatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("requester_id", "addressee_id", name="uq_friend_requests_pair"),
        sa.CheckConstraint("requester_id != addressee_id", name="ck_friend_requests_not_self"),
    )
    op.create_index("ix_friend_requests_addressee_status", "friend_requests", ["addressee_id", "status"])
    op.create_index("ix_friend_requests_requester_status", "friend_requests", ["requester_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_friend_requests_requester_status", table_name="friend_requests")
    op.drop_index("ix_friend_requests_addressee_status", table_name="friend_requests")
    op.drop_table("friend_requests")
