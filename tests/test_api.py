from datetime import datetime

from fastapi.testclient import TestClient

from app.api.extractions import get_extractor
from app.auth import CurrentUser, get_current_user
from app.main import app
from app.schemas import ExtractionResult


class StubExtractor:
    async def extract(self, **_):
        return ExtractionResult(
            title="Book Club",
            starts_at=datetime.fromisoformat("2026-07-12T18:30:00-05:00"),
            timezone="America/Chicago",
            location="Library",
            description="Chapter 4",
            confidence=0.95,
            warnings=[],
        )


TEST_USER = CurrentUser(
    id="ec4d34d4-7c45-4bad-9009-69d1215807cd", email="user@example.com", role="authenticated"
)


def test_health() -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_extraction_endpoint() -> None:
    app.dependency_overrides[get_extractor] = StubExtractor
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/extractions",
                files={"screenshot": ("event.png", b"image", "image/png")},
                data={"viewer_timezone": "America/Chicago"},
            )
        assert response.status_code == 200
        assert response.json()["title"] == "Book Club"
    finally:
        app.dependency_overrides.clear()


def test_extraction_rejects_non_image() -> None:
    app.dependency_overrides[get_extractor] = StubExtractor
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/extractions",
                files={"screenshot": ("event.txt", b"text", "text/plain")},
                data={"viewer_timezone": "America/Chicago"},
            )
        assert response.status_code == 415
    finally:
        app.dependency_overrides.clear()


def test_extraction_requires_authentication() -> None:
    app.dependency_overrides[get_extractor] = StubExtractor
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/extractions",
                files={"screenshot": ("event.png", b"image", "image/png")},
                data={"viewer_timezone": "America/Chicago"},
            )
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    finally:
        app.dependency_overrides.clear()
