from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.config import Settings, get_settings
from app.schemas import ExtractionResult
from app.services.extraction import EventExtractor, ExtractionError

router = APIRouter(prefix="/extractions", tags=["extractions"])
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def get_extractor(settings: Settings = Depends(get_settings)) -> EventExtractor:
    try:
        return EventExtractor(settings)
    except ExtractionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("", response_model=ExtractionResult)
async def extract_event(
    screenshot: UploadFile = File(...),
    viewer_timezone: str = Form(...),
    current_datetime: datetime | None = Form(default=None),
    settings: Settings = Depends(get_settings),
    extractor: EventExtractor = Depends(get_extractor),
) -> ExtractionResult:
    if screenshot.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Screenshot must be JPEG, PNG, WebP, or GIF",
        )
    try:
        ZoneInfo(viewer_timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=422, detail="Invalid IANA timezone") from exc

    image = await screenshot.read(settings.max_upload_bytes + 1)
    if not image:
        raise HTTPException(status_code=422, detail="Screenshot is empty")
    if len(image) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Screenshot is too large")

    try:
        return await extractor.extract(
            image=image,
            media_type=screenshot.content_type,
            viewer_timezone=viewer_timezone,
            now=current_datetime,
        )
    except ExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

