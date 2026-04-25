from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import FocusSession, Highlight


def get_active_focus(db: Session) -> Optional[FocusSession]:
    stmt = (
        select(FocusSession)
        .where(FocusSession.active_until > datetime.now(timezone.utc))
        .order_by(FocusSession.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def pick_random_highlight(db: Session) -> Optional[Highlight]:
    stmt = (
        select(Highlight)
        .options(joinedload(Highlight.book), joinedload(Highlight.tags))
        .order_by(func.random())
        .limit(1)
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def pick_focus_highlight(db: Session, focus: FocusSession) -> Optional[Highlight]:
    if focus.order_mode == "random":
        stmt = (
            select(Highlight)
            .options(joinedload(Highlight.book), joinedload(Highlight.tags))
            .where(Highlight.book_id == focus.book_id)
            .order_by(func.random())
            .limit(1)
        )
        return db.execute(stmt).unique().scalar_one_or_none()

    # sequential: ordered by id, using cursor
    total = db.execute(
        select(func.count()).select_from(Highlight).where(Highlight.book_id == focus.book_id)
    ).scalar_one()
    if total == 0:
        return None
    offset = focus.cursor % total
    stmt = (
        select(Highlight)
        .options(joinedload(Highlight.book), joinedload(Highlight.tags))
        .where(Highlight.book_id == focus.book_id)
        .order_by(Highlight.id.asc())
        .offset(offset)
        .limit(1)
    )
    hl = db.execute(stmt).unique().scalar_one_or_none()
    if hl is not None:
        focus.cursor = offset + 1
        db.add(focus)
        db.commit()
    return hl


def pick_highlight_for_today(db: Session) -> Optional[Highlight]:
    """Daily/random pick honoring an active focus session.

    - If focus mode == 'replace': always return from focused book.
    - If focus mode == 'augment': bias toward focused book (intensity / 5 chance).
    - No focus: random from all.
    """
    focus = get_active_focus(db)
    if focus is None:
        return pick_random_highlight(db)

    if focus.mode == "replace":
        hl = pick_focus_highlight(db, focus)
        return hl or pick_random_highlight(db)

    # augment: probabilistic bias
    import random

    chance = max(0.0, min(1.0, focus.intensity / 5.0))
    if random.random() < chance:
        hl = pick_focus_highlight(db, focus)
        if hl is not None:
            return hl
    return pick_random_highlight(db)
