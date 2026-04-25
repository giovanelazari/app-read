"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("asin", sa.String(20), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.Text()),
        sa.Column("cover_url", sa.Text()),
        sa.Column("last_synced", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "highlights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.Text()),
        sa.Column("color", sa.String(20)),
        sa.Column("note", sa.Text()),
        sa.Column("highlighted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("book_id", "location", "text", name="uq_highlight_book_loc_text"),
    )
    op.create_index("idx_highlights_book", "highlights", ["book_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "highlight_tags",
        sa.Column(
            "highlight_id",
            sa.Integer(),
            sa.ForeignKey("highlights.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "srs_state",
        sa.Column(
            "highlight_id",
            sa.Integer(),
            sa.ForeignKey("highlights.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("ef", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "next_review_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_srs_next", "srs_state", ["next_review_at"])

    op.create_table(
        "review_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "highlight_id",
            sa.Integer(),
            sa.ForeignKey("highlights.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ease", sa.SmallInteger(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("ef", sa.Float(), nullable=False),
        sa.CheckConstraint("ease BETWEEN 0 AND 5", name="ck_review_log_ease"),
    )

    op.create_table(
        "focus_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("active_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intensity", sa.SmallInteger(), nullable=False, server_default="3"),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("order_mode", sa.String(20), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("mode IN ('replace','augment')", name="ck_focus_mode"),
        sa.CheckConstraint("order_mode IN ('sequential','random')", name="ck_focus_order"),
    )

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("endpoint", sa.Text(), nullable=False, unique=True),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "sync_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("books_added", sa.Integer(), server_default="0"),
        sa.Column("highlights_added", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("sync_log")
    op.drop_table("push_subscriptions")
    op.drop_table("focus_sessions")
    op.drop_table("review_log")
    op.drop_index("idx_srs_next", table_name="srs_state")
    op.drop_table("srs_state")
    op.drop_table("highlight_tags")
    op.drop_table("tags")
    op.drop_index("idx_highlights_book", table_name="highlights")
    op.drop_table("highlights")
    op.drop_table("books")
