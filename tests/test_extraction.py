from datetime import datetime

import pytest

from app.config import Settings
from app.schemas import ExtractionResult
from app.services.extraction import EventExtractor, ExtractionError


class FakeResponses:
    def __init__(self, parsed: ExtractionResult | None) -> None:
        self.parsed = parsed
        self.request = None

    async def parse(self, **kwargs):
        self.request = kwargs
        return type("Response", (), {"output_parsed": self.parsed})()


class FakeClient:
    def __init__(self, parsed: ExtractionResult | None) -> None:
        self.responses = FakeResponses(parsed)


@pytest.mark.asyncio
async def test_extractor_sends_data_url_and_returns_structured_result() -> None:
    result = ExtractionResult(
        title="Neighborhood Picnic",
        ends_at=None,
        starts_at=datetime.fromisoformat("2026-07-11T12:00:00-05:00"),
        timezone="America/Chicago",
        location="Grant Park",
        description=None,
        confidence=0.91,
        warnings=[],
    )
    client = FakeClient(result)
    extractor = EventExtractor(Settings(openai_api_key="test"), client=client)  # type: ignore[arg-type]

    extracted = await extractor.extract(b"png", "image/png", "America/Chicago")

    assert extracted == result
    content = client.responses.request["input"][0]["content"]  # type: ignore[index]
    assert content[1]["image_url"].startswith("data:image/png;base64,")
    assert client.responses.request["text_format"] is ExtractionResult  # type: ignore[index]


def test_extractor_requires_api_key() -> None:
    with pytest.raises(ExtractionError, match="OPENAI_API_KEY"):
        EventExtractor(Settings(openai_api_key=None))


def test_incomplete_draft_is_reviewable() -> None:
    draft = ExtractionResult(
        title=None, starts_at=None, ends_at=None, timezone="UTC",
        location=None, description=None, confidence=0,
        warnings=["Enter a title and date before saving."],
    )
    assert draft.starts_at is None
