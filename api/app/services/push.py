import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pywebpush import WebPushException, webpush
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import PushSubscription

logger = logging.getLogger(__name__)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def ensure_vapid_keys() -> tuple[str, str]:
    """Generate an EC P-256 keypair for VAPID if none exists on disk.

    Returns (private_pem_path, public_key_b64url).
    """
    vapid_dir = Path(settings.vapid_dir)
    vapid_dir.mkdir(parents=True, exist_ok=True)
    priv_path = vapid_dir / "private_key.pem"
    pub_path = vapid_dir / "public_key.txt"

    if not priv_path.exists() or not pub_path.exists():
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        priv_path.write_bytes(pem)

        # VAPID expects raw uncompressed public key (65 bytes: 0x04 || X || Y), base64url without padding.
        public_numbers = private_key.public_key().public_numbers()
        x = public_numbers.x.to_bytes(32, "big")
        y = public_numbers.y.to_bytes(32, "big")
        raw = b"\x04" + x + y
        pub_path.write_text(_b64url(raw))
        logger.info("Generated new VAPID keypair at %s", vapid_dir)

    return str(priv_path), pub_path.read_text().strip()


def get_public_key() -> str:
    _, pub = ensure_vapid_keys()
    return pub


def send_push(db: Session, title: str, body: str, url: str | None = None, data: dict[str, Any] | None = None) -> int:
    """Send a push payload to all subscribers. Returns count of successful sends."""
    priv_path, _ = ensure_vapid_keys()
    payload = {"title": title, "body": body}
    if url:
        payload["url"] = url
    if data:
        payload.update(data)
    payload_str = json.dumps(payload)

    subs = db.execute(select(PushSubscription)).scalars().all()
    sent = 0
    stale: list[str] = []
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload_str,
                vapid_private_key=priv_path,
                vapid_claims={"sub": settings.vapid_claim_email},
            )
            sent += 1
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                stale.append(sub.endpoint)
            logger.warning("Push failed (status=%s): %s", status, exc)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected push error: %s", exc)

    if stale:
        db.execute(delete(PushSubscription).where(PushSubscription.endpoint.in_(stale)))
        db.commit()

    return sent
