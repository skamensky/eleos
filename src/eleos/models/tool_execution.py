from pydantic import BaseModel, Field

from eleos.models.payloads import RawToolPayload


class ToolRunResult(BaseModel):
    source: str
    summary: str
    raw_payload: RawToolPayload
    anomalies: list[str] = Field(default_factory=list)
    confidence_impact: float = 0.0
    novelty_signal: float = 0.0
    failed: bool = False
    error: str | None = None
