import uuid
from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VoteChoice(str, Enum):
    going = "going"
    maybe = "maybe"
    no = "no"


class EventFields(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str = Field(description="IANA timezone, for example America/Chicago")
    location: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_event_times(self) -> "EventFields":
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        if self.starts_at.tzinfo is None:
            raise ValueError("starts_at must include a UTC offset")
        if self.ends_at is not None:
            if self.ends_at.tzinfo is None:
                raise ValueError("ends_at must include a UTC offset")
            if self.ends_at <= self.starts_at:
                raise ValueError("ends_at must be after starts_at")
        return self


class EventCreate(EventFields):
    created_by: str = Field(min_length=1, max_length=200)


class EventUpdate(EventFields):
    pass


class VoteTotals(BaseModel):
    going: int = 0
    maybe: int = 0
    no: int = 0


class EventRead(EventFields):
    id: uuid.UUID
    created_by: str
    created_at: datetime
    updated_at: datetime
    vote_totals: VoteTotals
    group_ids: list[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class GroupRead(BaseModel):
    id: uuid.UUID
    name: str
    invite_code: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoteUpsert(BaseModel):
    voter_id: str = Field(min_length=1, max_length=200)
    choice: VoteChoice


class VoteRead(VoteUpsert):
    id: uuid.UUID
    event_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExtractionResult(EventFields):
    confidence: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)

