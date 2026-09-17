import secrets
import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas


async def create_group(
    db: AsyncSession, payload: schemas.GroupCreate, owner_id: uuid.UUID
) -> models.Group:
    group = models.Group(name=payload.name, invite_code=secrets.token_urlsafe(8))
    db.add(group)
    group.members.append(
        models.GroupMember(user_id=owner_id, role=models.GroupRole.owner)
    )
    await db.commit()
    await db.refresh(group)
    return group


async def get_group(db: AsyncSession, group_id: uuid.UUID) -> models.Group | None:
    return await db.get(models.Group, group_id)


async def get_group_by_invite(db: AsyncSession, invite_code: str) -> models.Group | None:
    return await db.scalar(select(models.Group).where(models.Group.invite_code == invite_code))


async def is_group_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    membership = await db.get(models.GroupMember, (group_id, user_id))
    return membership is not None


async def join_group(
    db: AsyncSession, group: models.Group, user_id: uuid.UUID
) -> models.GroupMember:
    group_id = group.id
    membership = await db.get(models.GroupMember, (group_id, user_id))
    if membership is None:
        membership = models.GroupMember(
            group_id=group.id, user_id=user_id, role=models.GroupRole.member
        )
        db.add(membership)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            membership = await db.get(models.GroupMember, (group_id, user_id))
            if membership is None:
                raise
        await db.refresh(membership)
    return membership


async def list_user_groups(
    db: AsyncSession, user_id: uuid.UUID
) -> list[tuple[models.Group, models.GroupRole]]:
    rows = await db.execute(
        select(models.Group, models.GroupMember.role)
        .join(models.GroupMember)
        .where(models.GroupMember.user_id == user_id)
        .order_by(models.Group.name)
    )
    return list(rows.tuples())


async def create_event(
    db: AsyncSession, payload: schemas.EventCreate, owner_id: uuid.UUID
) -> models.Event:
    event = models.Event(**payload.model_dump(), owner_id=owner_id)
    db.add(event)
    await db.commit()
    return await get_event(db, event.id)  # type: ignore[return-value]


async def get_event(db: AsyncSession, event_id: uuid.UUID) -> models.Event | None:
    return await db.scalar(
        select(models.Event)
        .where(models.Event.id == event_id)
        .options(selectinload(models.Event.groups), selectinload(models.Event.votes))
    )


async def list_group_events(db: AsyncSession, group_id: uuid.UUID) -> list[models.Event]:
    result = await db.scalars(
        select(models.Event)
        .join(models.EventGroup)
        .where(models.EventGroup.group_id == group_id)
        .options(selectinload(models.Event.groups), selectinload(models.Event.votes))
        .order_by(models.Event.starts_at)
    )
    return list(result.unique())


async def list_user_events(db: AsyncSession, user_id: uuid.UUID) -> list[models.Event]:
    result = await db.scalars(
        select(models.Event)
        .outerjoin(models.EventGroup)
        .outerjoin(
            models.GroupMember,
            and_(
                models.GroupMember.group_id == models.EventGroup.group_id,
                models.GroupMember.user_id == user_id,
            ),
        )
        .where(or_(models.Event.owner_id == user_id, models.GroupMember.user_id == user_id))
        .options(selectinload(models.Event.groups), selectinload(models.Event.votes))
        .order_by(models.Event.starts_at)
    )
    return list(result.unique())


async def user_can_access_event(
    db: AsyncSession, event: models.Event, user_id: uuid.UUID
) -> bool:
    if event.owner_id == user_id:
        return True
    membership = await db.scalar(
        select(models.GroupMember.group_id)
        .join(models.EventGroup, models.EventGroup.group_id == models.GroupMember.group_id)
        .where(
            models.EventGroup.event_id == event.id,
            models.GroupMember.user_id == user_id,
        )
        .limit(1)
    )
    return membership is not None


async def update_event(
    db: AsyncSession, event: models.Event, payload: schemas.EventUpdate
) -> models.Event:
    for field, value in payload.model_dump().items():
        setattr(event, field, value)
    await db.commit()
    return await get_event(db, event.id)  # type: ignore[return-value]


async def share_event(
    db: AsyncSession, event_id: uuid.UUID, group_id: uuid.UUID
) -> models.EventGroup:
    link = await db.get(models.EventGroup, (event_id, group_id))
    if link is None:
        link = models.EventGroup(event_id=event_id, group_id=group_id)
        db.add(link)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            link = await db.get(models.EventGroup, (event_id, group_id))
            if link is None:
                raise
        await db.refresh(link)
    return link


async def upsert_vote(
    db: AsyncSession, event_id: uuid.UUID, voter_id: uuid.UUID, payload: schemas.VoteUpsert
) -> models.Vote:
    vote = await db.scalar(
        select(models.Vote).where(
            models.Vote.event_id == event_id, models.Vote.voter_id == voter_id
        )
    )
    if vote is None:
        vote = models.Vote(
            event_id=event_id,
            voter_id=voter_id,
            choice=models.VoteChoice(payload.choice.value),
        )
        db.add(vote)
    else:
        vote.choice = models.VoteChoice(payload.choice.value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        vote = await db.scalar(
            select(models.Vote).where(
                models.Vote.event_id == event_id, models.Vote.voter_id == voter_id
            )
        )
        if vote is None:
            raise
        vote.choice = models.VoteChoice(payload.choice.value)
        await db.commit()
    await db.refresh(vote)
    return vote


async def get_vote_totals(db: AsyncSession, event_id: uuid.UUID) -> schemas.VoteTotals:
    rows = await db.execute(
        select(models.Vote.choice, func.count(models.Vote.id))
        .where(models.Vote.event_id == event_id)
        .group_by(models.Vote.choice)
    )
    counts = {choice.value: count for choice, count in rows}
    return schemas.VoteTotals(**counts)


async def serialize_event(
    db: AsyncSession, event: models.Event, viewer_id: uuid.UUID
) -> schemas.EventRead:
    vote_choice = await db.scalar(
        select(models.Vote.choice).where(
            models.Vote.event_id == event.id,
            models.Vote.voter_id == viewer_id,
        )
    )
    my_vote = schemas.VoteChoice(vote_choice.value) if vote_choice else None
    visible_groups = list(await db.scalars(
        select(models.EventGroup.group_id)
        .join(models.GroupMember, models.GroupMember.group_id == models.EventGroup.group_id)
        .where(models.EventGroup.event_id == event.id, models.GroupMember.user_id == viewer_id)
    ))
    return schemas.EventRead(
        **schemas.EventFields.model_validate(event, from_attributes=True).model_dump(),
        id=event.id,
        owner_id=event.owner_id,
        created_at=event.created_at,
        updated_at=event.updated_at,
        vote_totals=await get_vote_totals(db, event.id),
        my_vote=my_vote,
        group_ids=visible_groups,
    )
