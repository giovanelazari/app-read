from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class SRSResult:
    ef: float
    interval_days: int
    reps: int
    next_review_at: datetime


def sm2(
    ease: int,
    prev_ef: float = 2.5,
    prev_interval: int = 0,
    prev_reps: int = 0,
) -> SRSResult:
    """SM-2 (Piotr Wozniak). ease in 0..5.

    ease < 3 resets the repetition streak; ease >= 3 advances it.
    EF is kept unchanged on failure (common variant; avoids punishing newly-introduced items twice).
    """
    if ease < 0 or ease > 5:
        raise ValueError("ease must be 0..5")

    if ease < 3:
        new_reps = 0
        interval = 1
        new_ef = prev_ef
    else:
        new_ef = max(1.3, prev_ef + (0.1 - (5 - ease) * (0.08 + (5 - ease) * 0.02)))
        new_reps = prev_reps + 1
        if new_reps == 1:
            interval = 1
        elif new_reps == 2:
            interval = 6
        else:
            interval = max(1, round(prev_interval * new_ef))

    next_review = datetime.now(timezone.utc) + timedelta(days=interval)
    return SRSResult(ef=new_ef, interval_days=interval, reps=new_reps, next_review_at=next_review)
