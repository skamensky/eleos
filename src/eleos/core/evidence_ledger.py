from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from eleos.db import state_evidence, state_hypotheses, state_tools
from eleos.db.models import EvidenceRecordRow, ToolExecutionRow
from eleos.models.ids import CaseId, HypothesisId
from eleos.models.payloads import RawToolPayload
from eleos.models.tool_execution import ToolRunResult


def record(
    case_id: CaseId,
    result: ToolRunResult,
    tool_execution: ToolExecutionRow,
    linked_hypothesis_id: HypothesisId | None,
) -> EvidenceRecordRow:
    raw_json = json.dumps(result.raw_payload, sort_keys=True)
    raw_char_count = len(raw_json)
    evidence_id = str(uuid4())
    evidence = EvidenceRecordRow(
        evidence_id=evidence_id,
        case_id=str(case_id),
        tool_execution_id=tool_execution.tool_execution_id,
        source=result.source,
        finding_summary=result.summary,
        original_char_count=raw_char_count,
        anomalies=list(result.anomalies),
        confidence_impact=result.confidence_impact,
        novelty_signal=result.novelty_signal,
        raw_output_hash=sha256(raw_json.encode("utf-8")).hexdigest(),
        raw_output_size_bytes=len(raw_json.encode("utf-8")),
        detail_reason=None,
        created_at=datetime.now(timezone.utc),
    )
    state_evidence.save_raw_tool_payload(
        case_id=case_id,
        tool_execution_id=tool_execution.tool_execution_id,
        tool_name=tool_execution.tool_name,
        payload=result.raw_payload,
    )
    state_evidence.save_evidence(case_id, evidence)
    if linked_hypothesis_id is not None:
        state_hypotheses.add_hypothesis_evidence_link(
            case_id=case_id,
            hypothesis_id=linked_hypothesis_id,
            evidence_id=evidence_id,
            relation="task_linked",
        )
    return evidence


def attach_evidence_detail(
    evidence_id: str,
    raw_payload: RawToolPayload,
    reason: str,
) -> EvidenceRecordRow:
    evidence = state_evidence.get_evidence_record(evidence_id)
    case_id = state_evidence.case_id_for_evidence(evidence_id)
    tool_execution = state_tools.get_tool_execution(evidence.tool_execution_id)
    evidence.detail_reason = reason
    state_evidence.save_raw_tool_payload(
        case_id=case_id,
        tool_execution_id=evidence.tool_execution_id,
        tool_name=tool_execution.tool_name,
        payload=raw_payload,
    )
    state_evidence.save_evidence(case_id, evidence)
    return evidence


def get_evidence_raw(tool_execution_id: str) -> RawToolPayload:
    return state_evidence.get_raw_tool_payload(tool_execution_id)


def update_evidence_summary(
    evidence_id: str,
    summary: str,
    original_char_count: int,
) -> EvidenceRecordRow:
    evidence = state_evidence.get_evidence_record(evidence_id)
    case_id = state_evidence.case_id_for_evidence(evidence_id)
    evidence.finding_summary = summary
    evidence.original_char_count = original_char_count
    state_evidence.save_evidence(case_id, evidence)
    return evidence
