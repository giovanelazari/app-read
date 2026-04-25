from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from app.deps import DbSession
from app.models import Book, FocusSession
from app.schemas import FocusCreate, FocusOut

router = APIRouter(prefix="/focus", tags=["focus"])


def _active_stmt():
    return (
        select(FocusSession)
        .options(joinedload(FocusSession.book))
        .where(FocusSession.active_until > datetime.now(timezone.utc))
        .order_by(FocusSession.created_at.desc())
        .limit(1)
    )


@router.get("", response_model=FocusOut | None)
def get_active(db: DbSession):
    return db.execute(_active_stmt()).scalar_one_or_none()


@router.post("", response_model=FocusOut)
def create_focus(payload: FocusCreate, db: DbSession):
    if db.get(Book, payload.book_id) is None:
        raise HTTPException(404, "Book not found")

    # End any existing active focus before creating the new one.
    db.execute(
        delete(FocusSession).where(
            FocusSession.active_until > datetime.now(timezone.utc)
        )
    )

    session = FocusSession(
        book_id=payload.book_id,
        active_until=datetime.now(timezone.utc) + timedelta(days=payload.days),
        intensity=payload.intensity,
        mode=payload.mode,
        order_mode=payload.order_mode,
        cursor=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return db.execute(_active_stmt()).scalar_one()


@router.delete("", status_code=204)
def end_focus(db: DbSession):
    db.execute(
        delete(FocusSession).where(
            FocusSession.active_until > datetime.now(timezone.utc)
        )
    )
    db.commit()
    return None
