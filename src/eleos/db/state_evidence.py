from __future__ import annotations

from sqlalchemy import select

from eleos.db.engine import session_scope
from eleos.db.models import EvidenceRecordRow, ToolOutputRow
from eleos.db.state_support import initialize, lock_case_row, now_utc
from eleos.models.ids import CaseId, as_case_id
from eleos.models.payloads import RawToolPayload


def save_evidence(case_id: CaseId, evidence: EvidenceRecordRow) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        row = session.get(EvidenceRecordRow, evidence.evidence_id)
        if row is None:
            evidence.case_id = case_str
            session.add(evidence)
            return
        _write_evidence_row(row, case_str, evidence)


def list_evidence(case_id: CaseId) -> list[EvidenceRecordRow]:
    initialize()
    with session_scope() as session:
        return list(
            session.scalars(
                select(EvidenceRecordRow)
                .where(EvidenceRecordRow.case_id == str(case_id))
                .order_by(EvidenceRecordRow.created_at.asc(), EvidenceRecordRow.evidence_id.asc())
            ).all()
        )


def latest_evidence(case_id: CaseId) -> EvidenceRecordRow | None:
    initialize()
    with session_scope() as session:
        return session.scalars(
            select(EvidenceRecordRow)
            .where(EvidenceRecordRow.case_id == str(case_id))
            .order_by(EvidenceRecordRow.created_at.desc())
            .limit(1)
        ).first()


def has_evidence(case_id: CaseId) -> bool:
    initialize()
    with session_scope() as session:
        evidence_id = session.scalar(
            select(EvidenceRecordRow.evidence_id)
            .where(EvidenceRecordRow.case_id == str(case_id))
            .limit(1)
        )
        return evidence_id is not None


def list_evidence_ids(case_id: CaseId) -> list[str]:
    initialize()
    with session_scope() as session:
        return list(
            session.scalars(
                select(EvidenceRecordRow.evidence_id)
                .where(EvidenceRecordRow.case_id == str(case_id))
                .order_by(EvidenceRecordRow.created_at.asc(), EvidenceRecordRow.evidence_id.asc())
            ).all()
        )


def list_evidence_tool_execution_ids(case_id: CaseId) -> list[str]:
    initialize()
    with session_scope() as session:
        return list(
            session.scalars(
                select(EvidenceRecordRow.tool_execution_id)
                .where(EvidenceRecordRow.case_id == str(case_id))
                .order_by(EvidenceRecordRow.created_at.asc(), EvidenceRecordRow.evidence_id.asc())
            ).all()
        )


def get_evidence_record(evidence_id: str) -> EvidenceRecordRow:
    initialize()
    with session_scope() as session:
        row = session.get(EvidenceRecordRow, evidence_id)
        if row is None:
            raise KeyError(f"evidence not found: {evidence_id}")
        return row


def case_id_for_evidence(evidence_id: str) -> CaseId:
    initialize()
    with session_scope() as session:
        row = session.get(EvidenceRecordRow, evidence_id)
        if row is None:
            raise KeyError(f"evidence not found: {evidence_id}")
    return as_case_id(row.case_id)


def save_raw_tool_payload(
    case_id: CaseId,
    tool_execution_id: str,
    tool_name: str,
    payload: RawToolPayload,
) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        row = session.get(ToolOutputRow, tool_execution_id)
        if row is None:
            session.add(
                ToolOutputRow(
                    case_id=case_str,
                    tool_execution_id=tool_execution_id,
                    tool_name=tool_name,
                    payload_json=payload,
                )
            )
            return

        row.case_id = case_str
        row.tool_name = tool_name
        row.payload_json = payload
        row.updated_at = now_utc()


def get_raw_tool_payload(tool_execution_id: str) -> RawToolPayload:
    initialize()
    with session_scope() as session:
        row = session.get(ToolOutputRow, tool_execution_id)
        if row is None:
            raise KeyError(f"raw payload not found for tool_execution_id: {tool_execution_id}")
    return dict(row.payload_json)


def _write_evidence_row(row: EvidenceRecordRow, case_id: str, evidence: EvidenceRecordRow) -> None:
    row.case_id = case_id
    row.tool_execution_id = evidence.tool_execution_id
    row.source = evidence.source
    row.finding_summary = evidence.finding_summary
    row.original_char_count = evidence.original_char_count
    row.anomalies = list(evidence.anomalies)
    row.confidence_impact = evidence.confidence_impact
    row.novelty_signal = evidence.novelty_signal
    row.raw_output_hash = evidence.raw_output_hash
    row.raw_output_size_bytes = evidence.raw_output_size_bytes
    row.detail_reason = evidence.detail_reason
    row.created_at = evidence.created_at
    row.updated_at = now_utc()
