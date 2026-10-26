from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import get_extraction_service, get_repository
from app.main import app
from app.services.extraction import ExtractionOutputError


class FakeService:
    def extract(self, document_type: str, text: str):
        if text == "trigger invalid output":
            raise ExtractionOutputError("The model returned malformed data.")
        return type(
            "Result",
            (),
            {"model_dump": lambda self, mode: {"summary": "Confirma a reunião."}},
        )()


class FakeRepository:
    def save(self, document_type: str, data: dict):
        return uuid4(), datetime.now(timezone.utc)


app.dependency_overrides[get_extraction_service] = lambda: FakeService()
app.dependency_overrides[get_repository] = lambda: FakeRepository()
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_extraction_endpoint_returns_validated_payload():
    response = client.post(
        "/v1/extractions",
        json={"document_type": "email", "text": "Pode confirmar a reunião?"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["document_type"] == "email"
    assert body["data"]["summary"] == "Confirma a reunião."
    assert "id" in body


def test_empty_text_is_rejected():
    response = client.post(
        "/v1/extractions",
        json={"document_type": "email", "text": "  "},
    )
    assert response.status_code == 422


def test_oversized_text_is_rejected(monkeypatch):
    import app.api.routes as routes

    monkeypatch.setattr(routes, "settings", SimpleNamespace(max_input_chars=5))
    response = client.post(
        "/v1/extractions",
        json={"document_type": "email", "text": "texto grande"},
    )
    assert response.status_code == 413


def test_invalid_model_output_is_reported_to_client():
    response = client.post(
        "/v1/extractions",
        json={"document_type": "email", "text": "trigger invalid output"},
    )
    assert response.status_code == 502
    assert "malformed data" in response.json()["detail"]
