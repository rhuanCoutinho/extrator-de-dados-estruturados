from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.repositories.database import Base, ExtractionRepository, ExtractionRow


def test_repository_persists_structured_data():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        record_id, _ = ExtractionRepository(session).save(
            "invoice",
            {"invoice_number": "INV-42", "total": "12.50"},
        )
        saved = session.scalar(select(ExtractionRow).where(ExtractionRow.id == str(record_id)))

    assert saved is not None
    assert saved.document_type == "invoice"
    assert saved.data == {"invoice_number": "INV-42", "total": "12.50"}
    engine.dispose()
