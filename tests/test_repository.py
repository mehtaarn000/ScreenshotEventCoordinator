import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import repository, schemas
from app.database import Base


@pytest.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_members_can_access_shared_events(db) -> None:
    owner_id = uuid.uuid4()
    member_id = uuid.uuid4()
    group = await repository.create_group(db, schemas.GroupCreate(name="Friends"), owner_id)
    await repository.join_group(db, group, member_id)
    event = await repository.create_event(
        db,
        schemas.EventCreate(
            title="Picnic",
            starts_at=datetime.fromisoformat("2026-07-20T12:00:00-05:00"),
            timezone="America/Chicago",
        ),
        owner_id,
    )
    await repository.share_event(db, event.id, group.id)

    assert await repository.user_can_access_event(db, event, owner_id)
    assert await repository.user_can_access_event(db, event, member_id)
    assert not await repository.user_can_access_event(db, event, uuid.uuid4())


@pytest.mark.asyncio
async def test_vote_identity_comes_from_authenticated_user(db) -> None:
    owner_id = uuid.uuid4()
    event = await repository.create_event(
        db,
        schemas.EventCreate(
            title="Dinner",
            starts_at=datetime.fromisoformat("2026-07-20T18:00:00-05:00"),
            timezone="America/Chicago",
        ),
        owner_id,
    )

    vote = await repository.upsert_vote(
        db, event.id, owner_id, schemas.VoteUpsert(choice=schemas.VoteChoice.going)
    )
    updated = await repository.upsert_vote(
        db, event.id, owner_id, schemas.VoteUpsert(choice=schemas.VoteChoice.maybe)
    )

    assert vote.id == updated.id
    assert updated.voter_id == owner_id
    assert updated.choice.value == "maybe"

