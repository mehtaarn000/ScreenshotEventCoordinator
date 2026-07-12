import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import repository, schemas
from app.auth import CurrentUser, get_current_user
from app.database import get_db

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=schemas.GroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: schemas.GroupCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> schemas.GroupRead:
    group = await repository.create_group(db, payload, user.id)
    return schemas.GroupRead.model_validate(group)


@router.post("/join/{invite_code}", response_model=schemas.GroupRead)
async def join_group(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> schemas.GroupRead:
    group = await repository.get_group_by_invite(db, invite_code)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    await repository.join_group(db, group, user.id)
    return schemas.GroupRead.model_validate(group)


@router.get("/{group_id}/events", response_model=list[schemas.EventRead])
async def group_events(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> list[schemas.EventRead]:
    if await repository.get_group(db, group_id) is None:
        raise HTTPException(status_code=404, detail="Group not found")
    if not await repository.is_group_member(db, group_id, user.id):
        raise HTTPException(status_code=403, detail="Group membership required")
    events = await repository.list_group_events(db, group_id)
    return [await repository.serialize_event(db, event) for event in events]
