from typing import Literal

from pydantic import BaseModel, Field


class ReportSynthesisOutput(BaseModel):
    final_assessment: str
    confidence_label: Literal["low", "medium", "high"]
    escalation: str | None = None
    customer_followups: list[str] = Field(default_factory=list)
    internal_support_followups: list[str] = Field(default_factory=list)
