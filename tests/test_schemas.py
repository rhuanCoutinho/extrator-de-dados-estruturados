from pydantic import ValidationError
import pytest

from app.schemas.documents import EmailExtraction, InvoiceExtraction, ResumeExtraction


def test_email_schema_accepts_valid_data():
    result = EmailExtraction.model_validate(
        {
            "sender": "Ana <ana@example.com>",
            "recipients": ["Rui <rui@example.com>"],
            "subject": "Reunião",
            "sent_at": "2025-03-01T10:00:00Z",
            "summary": "Confirma a reunião de terça-feira.",
            "action_items": ["Enviar a pauta"],
            "urgency": "normal",
        }
    )
    assert result.urgency == "normal"
    assert result.recipients == ["Rui <rui@example.com>"]


def test_resume_rejects_unexpected_fields():
    with pytest.raises(ValidationError):
        ResumeExtraction.model_validate(
            {
                "full_name": "Joana Lima",
                "email": None,
                "phone": None,
                "location": None,
                "professional_summary": None,
                "skills": [],
                "experience": [],
                "education": [],
                "guessed_salary": 9999,
            }
        )


def test_invoice_rejects_invalid_date_and_amount():
    with pytest.raises(ValidationError):
        InvoiceExtraction.model_validate(
            {
                "vendor": "Papelaria Exemplo",
                "invoice_number": "NF-1",
                "issue_date": "ontem",
                "due_date": None,
                "currency": "BRL",
                "subtotal": "quarenta",
                "tax": None,
                "total": "40.00",
                "line_items": [],
            }
        )
