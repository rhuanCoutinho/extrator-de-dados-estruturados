"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.repositories.database import create_tables


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Structured Data Extractor",
    description="Extract and validate structured data from emails, resumes, and invoices.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}
