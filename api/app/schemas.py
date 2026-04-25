from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TagOut(ORMBase):
    id: int
    name: str


class TagCount(TagOut):
    count: int


class TagCreate(BaseModel):
    name: str


class TagsAssign(BaseModel):
    tags: list[str]


class BookOut(ORMBase):
    id: int
    asin: str
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    last_synced: Optional[datetime] = None


class BookWithCount(BookOut):
    highlights_count: int = 0


class HighlightOut(ORMBase):
    id: int
    book_id: int
    text: str
    location: Optional[str] = None
    color: Optional[str] = None
    note: Optional[str] = None
    highlighted_at: Optional[datetime] = None
    created_at: datetime
    book: BookOut
    tags: list[TagOut] = []


class ReviewRequest(BaseModel):
    ease: int = Field(ge=0, le=5)


class ReviewResult(BaseModel):
    highlight_id: int
    ef: float
    interval_days: int
    reps: int
    next_review_at: datetime


class FocusCreate(BaseModel):
    book_id: int
    days: int = Field(ge=1, le=365)
    intensity: int = Field(ge=1, le=5, default=3)
    mode: str = Field(pattern="^(replace|augment)$")
    order_mode: str = Field(pattern="^(sequential|random)$")


class FocusOut(ORMBase):
    id: int
    book_id: int
    active_until: datetime
    intensity: int
    mode: str
    order_mode: str
    cursor: int
    book: BookOut


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: PushKeys
    user_agent: Optional[str] = None


class PushUnsubscribe(BaseModel):
    endpoint: str


class VapidKey(BaseModel):
    public_key: str


class SyncStatus(BaseModel):
    id: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: Optional[str] = None
    books_added: int = 0
    highlights_added: int = 0
    error_message: Optional[str] = None
    running: bool = False
