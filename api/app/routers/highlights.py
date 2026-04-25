from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.deps import DbSession
from app.models import Highlight, ReviewLog, SRSState, Tag
from app.schemas import HighlightOut, ReviewRequest, ReviewResult, TagsAssign
from app.services import selector
from app.services.srs import sm2

router = APIRouter(prefix="/highlights", tags=["highlights"])


def _load(db, hl_id: int) -> Highlight:
    stmt = (
        select(Highlight)
        .options(joinedload(Highlight.book), joinedload(Highlight.tags))
        .where(Highlight.id == hl_id)
    )
    hl = db.execute(stmt).unique().scalar_one_or_none()
    if hl is None:
        raise HTTPException(404, "Highlight not found")
    return hl


@router.get("/today", response_model=HighlightOut)
def get_today(db: DbSession):
    hl = selector.pick_highlight_for_today(db)
    if hl is None:
        raise HTTPException(404, "No highlights available")
    return hl


@router.get("/random", response_model=HighlightOut)
def get_random(db: DbSession):
    hl = selector.pick_random_highlight(db)
    if hl is None:
        raise HTTPException(404, "No highlights available")
    return hl


@router.get("/review-queue", response_model=list[HighlightOut])
def review_queue(db: DbSession, limit: int = Query(10, ge=1, le=100)):
    now = datetime.now(timezone.utc)
    stmt = (
        select(Highlight)
        .join(SRSState, SRSState.highlight_id == Highlight.id)
        .options(joinedload(Highlight.book), joinedload(Highlight.tags))
        .where(SRSState.next_review_at <= now)
        .order_by(SRSState.next_review_at.asc())
        .limit(limit)
    )
    return db.execute(stmt).unique().scalars().all()


@router.post("/{hl_id}/review", response_model=ReviewResult)
def review(hl_id: int, payload: ReviewRequest, db: DbSession):
    hl = _load(db, hl_id)
    state = db.get(SRSState, hl_id)
    if state is None:
        state = SRSState(highlight_id=hl_id)
        db.add(state)
        db.flush()

    result = sm2(
        ease=payload.ease,
        prev_ef=state.ef,
        prev_interval=state.interval_days,
        prev_reps=state.reps,
    )
    state.ef = result.ef
    state.interval_days = result.interval_days
    state.reps = result.reps
    state.next_review_at = result.next_review_at
    state.last_reviewed_at = datetime.now(timezone.utc)

    db.add(
        ReviewLog(
            highlight_id=hl_id,
            ease=payload.ease,
            interval_days=result.interval_days,
            ef=result.ef,
        )
    )
    db.commit()
    db.refresh(state)

    return ReviewResult(
        highlight_id=hl_id,
        ef=state.ef,
        interval_days=state.interval_days,
        reps=state.reps,
        next_review_at=state.next_review_at,
    )


@router.get("/by-tag/{tag}", response_model=list[HighlightOut])
def by_tag(
    tag: str,
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = (
        select(Highlight)
        .join(Highlight.tags)
        .options(joinedload(Highlight.book), joinedload(Highlight.tags))
        .where(Tag.name == tag)
        .order_by(Highlight.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.execute(stmt).unique().scalars().all()


@router.post("/{hl_id}/tags", response_model=HighlightOut)
def assign_tags(hl_id: int, payload: TagsAssign, db: DbSession):
    hl = _load(db, hl_id)
    for name in payload.tags:
        norm = name.strip().lower()
        if not norm:
            continue
        tag = db.execute(select(Tag).where(Tag.name == norm)).scalar_one_or_none()
        if tag is None:
            tag = Tag(name=norm)
            db.add(tag)
            db.flush()
        if tag not in hl.tags:
            hl.tags.append(tag)
    db.commit()
    return _load(db, hl_id)


@router.delete("/{hl_id}/tags/{tag}", response_model=HighlightOut)
def remove_tag(hl_id: int, tag: str, db: DbSession):
    hl = _load(db, hl_id)
    norm = tag.strip().lower()
    hl.tags = [t for t in hl.tags if t.name != norm]
    db.commit()
    return _load(db, hl_id)
