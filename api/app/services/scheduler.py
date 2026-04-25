import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func, select

from app.config import settings
from app.database import SessionLocal
from app.models import Highlight, SRSState, SyncLog
from app.services import selector
from app.services.push import send_push

logger = logging.getLogger(__name__)


def send_daily_highlight() -> None:
    with SessionLocal() as db:
        hl = selector.pick_highlight_for_today(db)
        if hl is None:
            logger.info("No highlights yet — skipping daily push.")
            return
        title = f"{hl.book.title}"
        body = hl.text if len(hl.text) <= 200 else hl.text[:197] + "…"
        url = f"{settings.web_url}/?highlight={hl.id}"
        sent = send_push(db, title=title, body=body, url=url, data={"highlight_id": hl.id})
        logger.info("Daily highlight pushed to %d subscribers.", sent)


def send_review_reminder() -> None:
    with SessionLocal() as db:
        due = db.execute(
            select(func.count())
            .select_from(SRSState)
            .where(SRSState.next_review_at <= datetime.now(timezone.utc))
        ).scalar_one()
        if due == 0:
            logger.info("No reviews due — skipping reminder.")
            return
        title = "Revisão pendente"
        body = f"Você tem {due} grifo{'s' if due != 1 else ''} para revisar."
        url = f"{settings.web_url}/review"
        sent = send_push(db, title=title, body=body, url=url, data={"kind": "review"})
        logger.info("Review reminder (%d due) pushed to %d subscribers.", due, sent)


def run_sync_job() -> None:
    """Kick off a scrape. Imports inside the function to avoid loading Playwright at module import."""
    from app.scraper.kindle import run_scrape

    with SessionLocal() as db:
        log = SyncLog(status="running")
        db.add(log)
        db.commit()
        db.refresh(log)
        try:
            result = run_scrape(db)
            log.finished_at = datetime.now(timezone.utc)
            if result.auth_required:
                log.status = "auth_required"
                log.error_message = "Amazon session expired — re-run HEADED=1 scraper locally."
                send_push(
                    db,
                    title="Sessão Amazon expirou",
                    body="Renove o login rodando o scraper HEADED=1 localmente.",
                    url=f"{settings.web_url}/settings",
                    data={"kind": "auth_required"},
                )
            else:
                log.status = "success"
                log.books_added = result.books_added
                log.highlights_added = result.highlights_added
            db.add(log)
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Sync failed")
            log.finished_at = datetime.now(timezone.utc)
            log.status = "failed"
            log.error_message = str(exc)[:1000]
            db.add(log)
            db.commit()


def setup_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone=settings.timezone)

    sched.add_job(run_sync_job, CronTrigger(hour=6, minute=0), id="daily_sync")
    sched.add_job(send_daily_highlight, CronTrigger(hour=8, minute=0), id="daily_push")
    sched.add_job(
        send_review_reminder,
        CronTrigger(day_of_week="mon,wed,fri", hour=19, minute=0),
        id="review_reminder",
    )

    sched.start()
    logger.info("Scheduler started. Jobs: %s", [j.id for j in sched.get_jobs()])
    return sched
