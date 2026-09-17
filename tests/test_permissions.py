import uuid
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import repository, schemas
from app.auth import CurrentUser, get_current_user
from app.database import Base, get_db
from app.main import app


@pytest.fixture
async def scenario():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        owner, outsider = uuid.uuid4(), uuid.uuid4()
        event = await repository.create_event(db, schemas.EventCreate(
            title="Test", starts_at=datetime(2027, 1, 1, tzinfo=UTC), timezone="UTC"
        ), owner)

        async def session():
            yield db

        app.dependency_overrides[get_db] = session
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            id=outsider, role="authenticated"
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client, event.id, owner
        app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.parametrize("suffix,method", [
    ("", "GET"), ("", "DELETE"), ("/votes", "GET"), ("/vote", "DELETE"),
])
async def test_outsider_cannot_access_event(scenario, suffix, method):
    client, event_id, _ = scenario
    response = await client.request(method, f"/api/v1/events/{event_id}{suffix}")
    assert response.status_code == 403


async def test_owner_can_delete_event(scenario):
    client, event_id, owner = scenario
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=owner, role="authenticated"
    )
    response = await client.delete(f"/api/v1/events/{event_id}")
    assert response.status_code == 204
    assert (await client.get(f"/api/v1/events/{event_id}")).status_code == 404
