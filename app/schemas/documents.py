"""Pydantic schemas for supported document types."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EmailExtraction(StrictSchema):
    sender: str | None = Field(description="Email sender, including name if available")
    recipients: list[str] = Field(description="Recipients explicitly present in the message")
    subject: str | None
    sent_at: datetime | None = Field(description="Message date/time in ISO 8601 format")
    summary: str = Field(min_length=1, description="Concise summary of the email")
    action_items: list[str] = Field(description="Explicit requests or tasks mentioned")
    urgency: Literal["low", "normal", "high"]


class WorkExperience(StrictSchema):
    company: str | None
    role: str | None
    start_date: date | None
    end_date: date | None = Field(description="Null when current or not stated")
    description: str | None


class Education(StrictSchema):
    institution: str | None
    degree: str | None
    field_of_study: str | None
    start_date: date | None
    end_date: date | None


class ResumeExtraction(StrictSchema):
    full_name: str | None
    email: str | None
    phone: str | None
    location: str | None
    professional_summary: str | None
    skills: list[str]
    experience: list[WorkExperience]
    education: list[Education]


class InvoiceLineItem(StrictSchema):
    description: str
    quantity: Decimal | None
    unit_price: Decimal | None
    amount: Decimal | None


class InvoiceExtraction(StrictSchema):
    vendor: str | None
    invoice_number: str | None
    issue_date: date | None
    due_date: date | None
    currency: str | None = Field(description="Three-letter ISO 4217 code when known")
    subtotal: Decimal | None
    tax: Decimal | None
    total: Decimal | None
    line_items: list[InvoiceLineItem]


DocumentType: TypeAlias = Literal["email", "resume", "invoice"]
DocumentData: TypeAlias = EmailExtraction | ResumeExtraction | InvoiceExtraction

SCHEMA_BY_TYPE: dict[str, type[StrictSchema]] = {
    "email": EmailExtraction,
    "resume": ResumeExtraction,
    "invoice": InvoiceExtraction,
}
