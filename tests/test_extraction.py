import json

import pytest

from app.services.extraction import ExtractionOutputError, ExtractionService


class FakeGenerator:
    def __init__(self, responses: list[str]):
        self.responses = iter(responses)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return next(self.responses)


EMAIL = {
    "sender": "Carlos <carlos@example.com>",
    "recipients": [],
    "subject": "Prazo",
    "sent_at": None,
    "summary": "Solicita o envio do relatório.",
    "action_items": ["Enviar o relatório"],
    "urgency": "high",
}


def test_malformed_model_output_is_retried_with_validation_feedback():
    generator = FakeGenerator(["{not json", json.dumps(EMAIL)])
    result = ExtractionService(generator).extract("email", "Me envie o relatório hoje.")

    assert result.summary == EMAIL["summary"]
    assert len(generator.prompts) == 2
    assert "previous response failed validation" in generator.prompts[1]


def test_invalid_output_after_retry_raises_clear_error():
    generator = FakeGenerator(["not json", "still not json"])
    with pytest.raises(ExtractionOutputError, match="malformed data"):
        ExtractionService(generator).extract("email", "Texto de exemplo")
