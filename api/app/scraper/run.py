"""CLI entrypoint: `python -m app.scraper.run [--headed]`.

Use HEADED=1 (or --headed) the first time on your local machine to log in
to amazon.com.br. The saved profile can be SCP'd to the VPS for headless runs.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import SyncLog
from app.scraper.kindle import run_scrape

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("scraper.run")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headed", action="store_true", help="Launch visible browser for login.")
    args = parser.parse_args()

    if args.headed:
        os.environ["HEADED"] = "1"

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
                log.error_message = "Amazon session expired."
                logger.error("Auth required — re-run with --headed to log in.")
                db.add(log)
                db.commit()
                return 2
            log.status = "success"
            log.books_added = result.books_added
            log.highlights_added = result.highlights_added
            db.add(log)
            db.commit()
            logger.info(
                "Sync OK: %d new books, %d new highlights.",
                result.books_added,
                result.highlights_added,
            )
            return 0
        except Exception as exc:  # noqa: BLE001
            logger.exception("Sync failed")
            log.finished_at = datetime.now(timezone.utc)
            log.status = "failed"
            log.error_message = str(exc)[:1000]
            db.add(log)
            db.commit()
            return 1


if __name__ == "__main__":
    sys.exit(main())
