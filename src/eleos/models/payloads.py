from typing import Any

from pydantic import BaseModel

ToolInputPayload = dict[str, Any]


class ToolExecutionSummary(BaseModel):
    summary: str
    source: str
    failed: bool


RawToolPayload = dict[str, Any]


class EvidenceDetailPayload(BaseModel):
    reason: str
    payload: RawToolPayload
