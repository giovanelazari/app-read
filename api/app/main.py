import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import books, focus, highlights, push, review, sync, tags
from app.services.push import ensure_vapid_keys
from app.services.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_vapid_keys()
    scheduler = None
    if settings.scheduler_enabled:
        scheduler = setup_scheduler()
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(title="Kindle Highlights API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(highlights.router)
app.include_router(books.router)
app.include_router(review.router)
app.include_router(focus.router)
app.include_router(tags.router)
app.include_router(push.router)
app.include_router(sync.router)


@app.get("/healthz")
def healthz():
    return {"ok": True}
