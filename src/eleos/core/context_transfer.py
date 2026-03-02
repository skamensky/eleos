from __future__ import annotations

import json

from eleos.core.evidence_ledger import update_evidence_summary
from eleos.db.models import EvidenceRecordRow
from eleos.db.views.models import ToolSummaryInputView
from eleos.db.views.summarizer import build_tool_summary_input
from eleos.llm.agents.base.structured_agent import StructuredAgent
from eleos.llm.agents.summarizer.agent import tool_summarizer_agent
from eleos.models.agents.summarizer.models import ToolSummaryOutput

_summarizer_agent: StructuredAgent[ToolSummaryInputView, ToolSummaryOutput] = tool_summarizer_agent


def summarize_evidence(evidence: EvidenceRecordRow) -> EvidenceRecordRow:
    payload: ToolSummaryInputView = build_tool_summary_input(evidence.evidence_id)
    raw_char_count = len(json.dumps(payload.raw_payload, sort_keys=True))
    summarized = _summarizer_agent.run(payload)
    return update_evidence_summary(
        evidence_id=evidence.evidence_id,
        summary=summarized.summary,
        original_char_count=raw_char_count,
    )
