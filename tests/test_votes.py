import uuid
from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models, repository, schemas
from app.database import Base


async def test_repeated_rsvp_changes_and_withdrawal():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            voter = uuid.uuid4()
            event = await repository.create_event(db, schemas.EventCreate(
                title="Dinner", starts_at=datetime(2027, 1, 1, tzinfo=UTC), timezone="UTC"
            ), voter)
            for choice in ["going", "going", "maybe", "no"]:
                await repository.upsert_vote(db, event.id, voter, schemas.VoteUpsert(choice=choice))
                totals = await repository.get_vote_totals(db, event.id)
                assert sum(totals.model_dump().values()) == 1
                assert totals.model_dump()[choice] == 1
            await db.execute(delete(models.Vote).where(models.Vote.event_id == event.id))
            await db.commit()
            assert (await repository.get_vote_totals(db, event.id)).no == 0
    finally:
        await engine.dispose()
