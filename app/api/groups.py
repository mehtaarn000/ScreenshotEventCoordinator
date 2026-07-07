import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import repository, schemas
from app.database import get_db

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=schemas.GroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: schemas.GroupCreate, db: AsyncSession = Depends(get_db)
) -> schemas.GroupRead:
    return schemas.GroupRead.model_validate(await repository.create_group(db, payload))


@router.get("/join/{invite_code}", response_model=schemas.GroupRead)
async def resolve_invite(
    invite_code: str, db: AsyncSession = Depends(get_db)
) -> schemas.GroupRead:
    group = await repository.get_group_by_invite(db, invite_code)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return schemas.GroupRead.model_validate(group)


@router.get("/{group_id}/events", response_model=list[schemas.EventRead])
async def group_events(
    group_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[schemas.EventRead]:
    if await repository.get_group(db, group_id) is None:
        raise HTTPException(status_code=404, detail="Group not found")
    events = await repository.list_group_events(db, group_id)
    return [await repository.serialize_event(db, event) for event in events]

