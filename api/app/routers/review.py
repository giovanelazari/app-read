from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import func, select

from app.deps import DbSession
from app.models import SRSState

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/stats")
def stats(db: DbSession):
    now = datetime.now(timezone.utc)
    due = db.execute(
        select(func.count()).select_from(SRSState).where(SRSState.next_review_at <= now)
    ).scalar_one()
    total = db.execute(select(func.count()).select_from(SRSState)).scalar_one()
    return {"due": due, "total": total}
