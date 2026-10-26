"""SQLAlchemy database setup and extraction repository."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


def _database_url() -> str:
    url = settings.database_url
    # Render may expose the legacy scheme; psycopg 3 is used for PostgreSQL.
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


db_url = _database_url()
engine_options: dict = {"pool_pre_ping": True}
if db_url.startswith("sqlite:"):
    engine_options["connect_args"] = {"check_same_thread": False}
    if db_url.endswith(":memory:") or db_url.endswith("/:memory:"):
        engine_options["poolclass"] = StaticPool
    elif db_url.startswith("sqlite:///./"):
        Path(db_url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(db_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ExtractionRow(Base):
    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExtractionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, document_type: str, data: dict) -> tuple[UUID, datetime]:
        record_id = uuid4()
        created_at = datetime.now(timezone.utc)
        row = ExtractionRow(
            id=str(record_id),
            document_type=document_type,
            data=data,
            created_at=created_at,
        )
        self.session.add(row)
        self.session.commit()
        return record_id, created_at


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
