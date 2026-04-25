from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.deps import DbSession
from app.models import Book, Highlight
from app.schemas import BookOut, BookWithCount, HighlightOut

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookWithCount])
def list_books(db: DbSession):
    stmt = (
        select(Book, func.count(Highlight.id).label("hl_count"))
        .outerjoin(Highlight, Highlight.book_id == Book.id)
        .group_by(Book.id)
        .order_by(Book.title.asc())
    )
    rows = db.execute(stmt).all()
    return [
        BookWithCount(
            id=b.id,
            asin=b.asin,
            title=b.title,
            author=b.author,
            cover_url=b.cover_url,
            last_synced=b.last_synced,
            highlights_count=count,
        )
        for b, count in rows
    ]


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: DbSession):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(404, "Book not found")
    return book


@router.get("/{book_id}/highlights", response_model=list[HighlightOut])
def get_book_highlights(
    book_id: int,
    db: DbSession,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    if db.get(Book, book_id) is None:
        raise HTTPException(404, "Book not found")
    stmt = (
        select(Highlight)
        .options(joinedload(Highlight.book), joinedload(Highlight.tags))
        .where(Highlight.book_id == book_id)
        .order_by(Highlight.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return db.execute(stmt).unique().scalars().all()
