from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import EventCreate


def test_event_requires_ordered_times() -> None:
    with pytest.raises(ValidationError, match="ends_at must be after"):
        EventCreate(
            title="Concert",
            starts_at=datetime.fromisoformat("2026-07-10T20:00:00-05:00"),
            ends_at=datetime.fromisoformat("2026-07-10T19:00:00-05:00"),
            timezone="America/Chicago",
        )


def test_event_rejects_unknown_timezone() -> None:
    with pytest.raises(ValidationError, match="valid IANA timezone"):
        EventCreate(
            title="Concert",
            starts_at=datetime.fromisoformat("2026-07-10T20:00:00-05:00"),
            timezone="Central-ish",
        )
