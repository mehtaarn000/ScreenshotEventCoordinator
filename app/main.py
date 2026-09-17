from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import events, extractions, groups
from app.config import get_settings
from app.database import engine, get_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(events.router, prefix=settings.api_prefix)
app.include_router(extractions.router, prefix=settings.api_prefix)
app.include_router(groups.router, prefix=settings.api_prefix)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
async def ready(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready"}
