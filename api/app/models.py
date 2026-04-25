from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asin: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(Text)
    cover_url: Mapped[Optional[str]] = mapped_column(Text)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    highlights: Mapped[list["Highlight"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )


class Highlight(Base):
    __tablename__ = "highlights"
    __table_args__ = (
        UniqueConstraint("book_id", "location", "text", name="uq_highlight_book_loc_text"),
        Index("idx_highlights_book", "book_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(20))
    note: Mapped[Optional[str]] = mapped_column(Text)
    highlighted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    book: Mapped[Book] = relationship(back_populates="highlights")
    srs: Mapped[Optional["SRSState"]] = relationship(
        back_populates="highlight", cascade="all, delete-orphan", uselist=False
    )
    tags: Mapped[list["Tag"]] = relationship(secondary="highlight_tags", back_populates="highlights")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    highlights: Mapped[list[Highlight]] = relationship(
        secondary="highlight_tags", back_populates="tags"
    )


class HighlightTag(Base):
    __tablename__ = "highlight_tags"

    highlight_id: Mapped[int] = mapped_column(
        ForeignKey("highlights.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class SRSState(Base):
    __tablename__ = "srs_state"

    highlight_id: Mapped[int] = mapped_column(
        ForeignKey("highlights.id", ondelete="CASCADE"), primary_key=True
    )
    ef: Mapped[float] = mapped_column(nullable=False, default=2.5, server_default="2.5")
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    reps: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_review_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    highlight: Mapped[Highlight] = relationship(back_populates="srs")


Index("idx_srs_next", SRSState.next_review_at)


class ReviewLog(Base):
    __tablename__ = "review_log"
    __table_args__ = (CheckConstraint("ease BETWEEN 0 AND 5", name="ck_review_log_ease"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    highlight_id: Mapped[int] = mapped_column(
        ForeignKey("highlights.id", ondelete="CASCADE"), nullable=False
    )
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ease: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    ef: Mapped[float] = mapped_column(nullable=False)


class FocusSession(Base):
    __tablename__ = "focus_sessions"
    __table_args__ = (
        CheckConstraint("mode IN ('replace','augment')", name="ck_focus_mode"),
        CheckConstraint("order_mode IN ('sequential','random')", name="ck_focus_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    active_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    intensity: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    order_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    cursor: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    book: Mapped[Book] = relationship()


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    endpoint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncLog(Base):
    __tablename__ = "sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    books_added: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    highlights_added: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    error_message: Mapped[Optional[str]] = mapped_column(Text)


@event.listens_for(Highlight, "after_insert")
def _create_srs_state(mapper, connection, target: Highlight) -> None:
    """Ensure every new highlight gets a default SRS row (due now)."""
    connection.execute(
        SRSState.__table__.insert().values(
            highlight_id=target.id,
            ef=2.5,
            interval_days=0,
            reps=0,
            next_review_at=func.now(),
        )
    )
