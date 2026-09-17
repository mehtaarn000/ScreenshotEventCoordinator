import uuid
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VoteChoice(StrEnum):
    going = "going"
    maybe = "maybe"
    no = "no"


class GroupRole(StrEnum):
    owner = "owner"
    member = "member"


class EventFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
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
        except (ZoneInfoNotFoundError, ValueError) as exc:
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
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EventUpdate(EventFields):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class VoteTotals(BaseModel):
    going: int = 0
    maybe: int = 0
    no: int = 0


class EventRead(EventFields):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    vote_totals: VoteTotals
    my_vote: VoteChoice | None
    group_ids: list[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)


class GroupCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)


class GroupRead(BaseModel):
    id: uuid.UUID
    name: str
    invite_code: str
    created_at: datetime
    role: GroupRole

    model_config = ConfigDict(from_attributes=True)


class VoteUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    choice: VoteChoice


class VoteRead(VoteUpsert):
    id: uuid.UUID
    event_id: uuid.UUID
    voter_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExtractionResult(BaseModel):
    """Unconfirmed draft: missing facts remain empty until the user reviews them."""

    title: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    timezone: str
    location: str | None
    description: str | None
    confidence: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)
