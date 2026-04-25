"""Playwright-based scraper for read.amazon.com/kp/notebook.

- Uses a persistent browser context so login state (cookies, localStorage) survives.
- First run with HEADED=1 to do the interactive login + 2FA, then reuse the saved profile headless.
- Idempotent: inserts use ON CONFLICT DO NOTHING on (book_id, location, text).
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Page, TimeoutError as PWTimeout, sync_playwright
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models import Book, Highlight

logger = logging.getLogger(__name__)

NOTEBOOK_URLS = [
    "https://read.amazon.com/kp/notebook",
    "https://read.amazon.com.br/kp/notebook",
]
SIGNIN_MARKER = "ap/signin"


@dataclass
class ScrapeResult:
    books_added: int = 0
    highlights_added: int = 0
    auth_required: bool = False


def _launch(pw, headed: bool) -> BrowserContext:
    profile_dir = Path(settings.playwright_profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    # Optional proxy. Set SCRAPER_PROXY (e.g. "socks5://127.0.0.1:1080") when doing
    # the headed login locally through an SSH dynamic forward to the VPS, so Amazon
    # sees the VPS's IP from the initial login and binds the cookies to it.
    proxy_url = os.environ.get("SCRAPER_PROXY")
    proxy = {"server": proxy_url} if proxy_url else None
    if proxy:
        logger.info("Using proxy: %s", proxy_url)
    context = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=not headed,
        viewport={"width": 1280, "height": 900},
        locale="pt-BR",
        args=["--disable-blink-features=AutomationControlled"],
        proxy=proxy,
    )
    return context


def _open_notebook(page: Page) -> bool:
    """Navigate to the Kindle notebook. Return True if logged in, False if login is required."""
    last_err: Exception | None = None
    for url in NOTEBOOK_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if SIGNIN_MARKER in page.url:
                return False
            # Wait for the library list to render.
            page.wait_for_selector(".kp-notebook-library-each-book", timeout=20000)
            return True
        except PWTimeout as exc:
            last_err = exc
            continue
    if last_err:
        raise last_err
    return False


def _extract_books(page: Page) -> list[dict]:
    books = page.eval_on_selector_all(
        ".kp-notebook-library-each-book",
        """
        els => els.map(el => {
            const asin = el.getAttribute('id') || el.getAttribute('data-asin') || '';
            const titleEl = el.querySelector('h2.kp-notebook-searchable, .kp-notebook-library-each-book h2, h2');
            const authorEl = el.querySelector('p.kp-notebook-searchable, .a-spacing-base p');
            const img = el.querySelector('img');
            return {
                asin: asin,
                title: titleEl ? titleEl.textContent.trim() : '',
                author: authorEl ? authorEl.textContent.trim() : null,
                cover_url: img ? img.src : null,
            };
        })
        """,
    )
    return [b for b in books if b["asin"] and b["title"]]


def _extract_highlights(page: Page, asin: str) -> list[dict]:
    # Click the book entry by its id, wait for the right-hand panel to load.
    page.click(f"#{asin}")
    page.wait_for_selector("#kp-notebook-annotations .a-row.a-spacing-base", timeout=20000)
    # Scroll to force lazy-load of all highlights.
    for _ in range(30):
        prev = page.evaluate("document.querySelectorAll('#kp-notebook-annotations .a-row.a-spacing-base').length")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        now = page.evaluate("document.querySelectorAll('#kp-notebook-annotations .a-row.a-spacing-base').length")
        if now == prev:
            break

    return page.eval_on_selector_all(
        "#kp-notebook-annotations .a-row.a-spacing-base",
        """
        els => els.map(el => {
            const textEl = el.querySelector('#highlight, .kp-notebook-highlight, span#highlight');
            const noteEl = el.querySelector('#note, .kp-notebook-note');
            const locEl = el.querySelector('#annotationHighlightHeader, .kp-notebook-metadata');
            const colorEl = el.querySelector('.kp-notebook-highlight');
            let color = null;
            if (colorEl) {
                const cls = colorEl.className || '';
                const m = cls.match(/kp-notebook-highlight-(\\w+)/);
                if (m) color = m[1];
            }
            return {
                text: textEl ? textEl.textContent.trim() : '',
                note: noteEl ? noteEl.textContent.trim() : null,
                location: locEl ? locEl.textContent.trim() : null,
                color: color,
            };
        }).filter(h => h.text && h.text.length > 0)
        """,
    )


def _upsert_book(db: Session, data: dict) -> tuple[Book, bool]:
    book = db.execute(select(Book).where(Book.asin == data["asin"])).scalar_one_or_none()
    created = False
    if book is None:
        book = Book(
            asin=data["asin"],
            title=data["title"],
            author=data.get("author"),
            cover_url=data.get("cover_url"),
        )
        db.add(book)
        db.flush()
        created = True
    else:
        # Refresh mutable fields.
        book.title = data["title"] or book.title
        if data.get("author"):
            book.author = data["author"]
        if data.get("cover_url"):
            book.cover_url = data["cover_url"]
    book.last_synced = datetime.now(timezone.utc)
    db.flush()
    return book, created


def _insert_highlights(db: Session, book: Book, items: list[dict]) -> int:
    if not items:
        return 0
    added = 0
    for it in items:
        stmt = (
            pg_insert(Highlight)
            .values(
                book_id=book.id,
                text=it["text"],
                location=it.get("location"),
                color=it.get("color"),
                note=it.get("note"),
            )
            .on_conflict_do_nothing(
                index_elements=["book_id", "location", "text"]
            )
            .returning(Highlight.id)
        )
        result = db.execute(stmt).scalar_one_or_none()
        if result is not None:
            added += 1
    db.commit()
    return added


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    reraise=True,
)
def _scrape_once(db: Session, headed: bool) -> ScrapeResult:
    result = ScrapeResult()
    with sync_playwright() as pw:
        context = _launch(pw, headed=headed)
        page = context.new_page()
        try:
            logged_in = _open_notebook(page)
            if not logged_in:
                if headed:
                    logger.warning("Not logged in. Complete login in the browser window; scraper will wait.")
                    # Give the user up to 5 minutes to finish login + 2FA, then retry navigation.
                    page.wait_for_url(lambda u: "/kp/notebook" in u, timeout=300_000)
                    logged_in = _open_notebook(page)
                if not logged_in:
                    result.auth_required = True
                    return result

            books = _extract_books(page)
            logger.info("Found %d books in Kindle library.", len(books))

            for b in books:
                try:
                    book_row, created = _upsert_book(db, b)
                    if created:
                        result.books_added += 1
                    highlights = _extract_highlights(page, b["asin"])
                    added = _insert_highlights(db, book_row, highlights)
                    result.highlights_added += added
                    logger.info(
                        "%s: %d highlights scraped, %d new.",
                        b["title"][:60],
                        len(highlights),
                        added,
                    )
                    time.sleep(1.5)  # gentle rate-limit
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Failed book %s: %s", b.get("asin"), exc)
                    continue
        finally:
            context.close()
    return result


def run_scrape(db: Session, headed: bool | None = None) -> ScrapeResult:
    if headed is None:
        headed = os.environ.get("HEADED") == "1"
    return _scrape_once(db, headed=headed)
