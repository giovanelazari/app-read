from fastapi import APIRouter, Request
from sqlalchemy import delete, select

from app.deps import DbSession
from app.models import PushSubscription
from app.schemas import PushSubscriptionIn, PushUnsubscribe, VapidKey
from app.services.push import get_public_key

router = APIRouter(prefix="/push", tags=["push"])


@router.get("/vapid-public-key", response_model=VapidKey)
def vapid_public_key():
    return VapidKey(public_key=get_public_key())


@router.post("/subscribe", status_code=201)
def subscribe(payload: PushSubscriptionIn, request: Request, db: DbSession):
    existing = db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
    ).scalar_one_or_none()
    if existing:
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
        existing.user_agent = payload.user_agent or request.headers.get("user-agent")
    else:
        db.add(
            PushSubscription(
                endpoint=payload.endpoint,
                p256dh=payload.keys.p256dh,
                auth=payload.keys.auth,
                user_agent=payload.user_agent or request.headers.get("user-agent"),
            )
        )
    db.commit()
    return {"status": "ok"}


@router.delete("/subscribe", status_code=204)
def unsubscribe(payload: PushUnsubscribe, db: DbSession):
    db.execute(delete(PushSubscription).where(PushSubscription.endpoint == payload.endpoint))
    db.commit()
    return None
