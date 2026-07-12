import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import repository, schemas
from app.auth import CurrentUser, get_current_user
from app.database import get_db

router = APIRouter(prefix="/events", tags=["events"])


async def event_or_404(db: AsyncSession, event_id: uuid.UUID):
    event = await repository.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def owned_event_or_403(db: AsyncSession, event_id: uuid.UUID, user: CurrentUser):
    event = await event_or_404(db, event_id)
    if event.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this event")
    return event


@router.post("", response_model=schemas.EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: schemas.EventCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> schemas.EventRead:
    event = await repository.create_event(db, payload, user.id)
    return await repository.serialize_event(db, event)


@router.get("/{event_id}", response_model=schemas.EventRead)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> schemas.EventRead:
    return await repository.serialize_event(db, await owned_event_or_403(db, event_id, user))


@router.put("/{event_id}", response_model=schemas.EventRead)
async def update_event(
    event_id: uuid.UUID,
    payload: schemas.EventUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> schemas.EventRead:
    event = await repository.update_event(
        db, await owned_event_or_403(db, event_id, user), payload
    )
    return await repository.serialize_event(db, event)


@router.put("/{event_id}/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def share_event(
    event_id: uuid.UUID,
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> Response:
    await owned_event_or_403(db, event_id, user)
    if await repository.get_group(db, group_id) is None:
        raise HTTPException(status_code=404, detail="Group not found")
    await repository.share_event(db, event_id, group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{event_id}/vote", response_model=schemas.VoteRead)
async def vote(
    event_id: uuid.UUID,
    payload: schemas.VoteUpsert,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> schemas.VoteRead:
    await owned_event_or_403(db, event_id, user)
    vote = await repository.upsert_vote(db, event_id, user.id, payload)
    return schemas.VoteRead.model_validate(vote)


@router.get("/{event_id}/votes", response_model=schemas.VoteTotals)
async def vote_totals(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> schemas.VoteTotals:
    await owned_event_or_403(db, event_id, user)
    return await repository.get_vote_totals(db, event_id)
