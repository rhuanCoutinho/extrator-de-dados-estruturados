"""HTTP endpoints and dependency wiring."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.database import ExtractionRepository, SessionLocal
from app.schemas.documents import DocumentType
from app.services.extraction import (
    ExtractionOutputError,
    ExtractionProviderError,
    ExtractionService,
    get_extraction_service,
)

router = APIRouter()


class ExtractionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    document_type: DocumentType
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class ExtractionResponse(BaseModel):
    id: UUID
    document_type: DocumentType
    data: dict[str, Any]
    created_at: datetime


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_repository(session: Session = Depends(get_db)) -> ExtractionRepository:
    return ExtractionRepository(session)


@router.post("/v1/extractions", response_model=ExtractionResponse, status_code=201)
def create_extraction(
    request: ExtractionRequest,
    service: ExtractionService = Depends(get_extraction_service),
    repository: ExtractionRepository = Depends(get_repository),
) -> ExtractionResponse:
    if len(request.text) > settings.max_input_chars:
        raise HTTPException(
            status_code=413,
            detail=f"text exceeds the {settings.max_input_chars}-character limit",
        )
    try:
        result = service.extract(request.document_type, request.text)
    except ExtractionOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ExtractionProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    record_id, created_at = repository.save(
        request.document_type,
        result.model_dump(mode="json"),
    )
    return ExtractionResponse(
        id=record_id,
        document_type=request.document_type,
        data=result.model_dump(mode="json"),
        created_at=created_at,
    )
