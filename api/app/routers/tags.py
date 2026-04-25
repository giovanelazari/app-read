from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.deps import DbSession
from app.models import Highlight, HighlightTag, Tag
from app.schemas import TagCount, TagCreate, TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagCount])
def list_tags(db: DbSession):
    stmt = (
        select(Tag, func.count(HighlightTag.highlight_id).label("cnt"))
        .outerjoin(HighlightTag, HighlightTag.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.name.asc())
    )
    rows = db.execute(stmt).all()
    return [TagCount(id=t.id, name=t.name, count=count) for t, count in rows]


@router.post("", response_model=TagOut, status_code=201)
def create_tag(payload: TagCreate, db: DbSession):
    norm = payload.name.strip().lower()
    if not norm:
        raise HTTPException(400, "Tag name cannot be empty")
    existing = db.execute(select(Tag).where(Tag.name == norm)).scalar_one_or_none()
    if existing:
        return existing
    tag = Tag(name=norm)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag
