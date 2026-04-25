from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import select

from app.deps import DbSession
from app.models import SyncLog
from app.schemas import SyncStatus

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", status_code=202)
def trigger_sync(background: BackgroundTasks, db: DbSession):
    running = db.execute(
        select(SyncLog).where(SyncLog.status == "running").limit(1)
    ).scalar_one_or_none()
    if running:
        return {"status": "already_running", "sync_id": running.id}

    from app.services.scheduler import run_sync_job

    background.add_task(run_sync_job)
    return {"status": "scheduled"}


@router.get("/status", response_model=SyncStatus)
def sync_status(db: DbSession):
    last = db.execute(select(SyncLog).order_by(SyncLog.id.desc()).limit(1)).scalar_one_or_none()
    running = db.execute(
        select(SyncLog).where(SyncLog.status == "running").limit(1)
    ).scalar_one_or_none()
    if last is None:
        return SyncStatus(running=running is not None)
    return SyncStatus(
        id=last.id,
        started_at=last.started_at,
        finished_at=last.finished_at,
        status=last.status,
        books_added=last.books_added or 0,
        highlights_added=last.highlights_added or 0,
        error_message=last.error_message,
        running=running is not None,
    )
