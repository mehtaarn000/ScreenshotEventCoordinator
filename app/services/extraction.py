import base64
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI

from app.config import Settings
from app.schemas import ExtractionResult

EXTRACTION_PROMPT = """Extract the event shown in this screenshot.
Return the title, start and optional end timestamps, IANA timezone, location, and description.
Use the supplied viewer timezone when the screenshot does not identify one. Resolve relative dates
against the supplied current datetime. Never invent missing venue or description text: return null.
Include a 0-1 confidence score and concise warnings for ambiguity or missing important information.
Timestamps must be ISO 8601 values with UTC offsets."""


class ExtractionError(RuntimeError):
    pass


class EventExtractor:
    def __init__(self, settings: Settings, client: AsyncOpenAI | None = None) -> None:
        if client is None and not settings.openai_api_key:
            raise ExtractionError("OPENAI_API_KEY is not configured")
        self.client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_vision_model

    async def extract(
        self,
        image: bytes,
        media_type: str,
        viewer_timezone: str,
        now: datetime | None = None,
    ) -> ExtractionResult:
        current = now or datetime.now(ZoneInfo(viewer_timezone))
        encoded = base64.b64encode(image).decode("ascii")
        data_url = f"data:{media_type};base64,{encoded}"
        try:
            response = await self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    f"{EXTRACTION_PROMPT}\nViewer timezone: {viewer_timezone}. "
                                    f"Current datetime: {current.isoformat()}."
                                ),
                            },
                            {"type": "input_image", "image_url": data_url, "detail": "high"},
                        ],
                    }
                ],
                text_format=ExtractionResult,
            )
        except Exception as exc:
            raise ExtractionError("The screenshot could not be extracted") from exc

        if response.output_parsed is None:
            raise ExtractionError("The model did not return event details")
        return response.output_parsed

