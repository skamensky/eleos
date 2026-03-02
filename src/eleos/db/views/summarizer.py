from __future__ import annotations

from eleos.db import state_evidence
from eleos.db.views.mappers import to_evidence_view
from eleos.db.views.models import ToolSummaryInputView


def build_tool_summary_input(evidence_id: str) -> ToolSummaryInputView:
    evidence = state_evidence.get_evidence_record(evidence_id)
    raw_payload = state_evidence.get_raw_tool_payload(evidence.tool_execution_id)
    return ToolSummaryInputView(
        evidence=to_evidence_view(evidence),
        raw_payload=raw_payload,
    )
