from __future__ import annotations

from sqlalchemy import func, select

from eleos.db.engine import session_scope
from eleos.db.models import EvidenceRecordRow, HypothesisEvidenceLinkRow, HypothesisRow
from eleos.db.state_support import initialize, lock_case_row
from eleos.models.enums import HypothesisStatus
from eleos.models.ids import CaseId, HypothesisId, as_hypothesis_id


def save_hypotheses(case_id: CaseId, hypotheses: list[HypothesisRow]) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        existing = {
            row.hypothesis_id: row
            for row in session.scalars(
                select(HypothesisRow).where(HypothesisRow.case_id == case_str)
            ).all()
        }
        for hypothesis in hypotheses:
            hypothesis.case_id = case_str
            row = existing.pop(hypothesis.hypothesis_id, None)
            if row is None:
                session.add(hypothesis)
            else:
                _write_hypothesis_row(row, hypothesis)

        for stale in existing.values():
            session.delete(stale)


def list_hypotheses(case_id: CaseId) -> list[HypothesisRow]:
    initialize()
    with session_scope() as session:
        return list(
            session.scalars(
                select(HypothesisRow)
                .where(HypothesisRow.case_id == str(case_id))
                .order_by(HypothesisRow.last_updated_at.asc())
            ).all()
        )


def list_hypothesis_ids(case_id: CaseId) -> list[HypothesisId]:
    initialize()
    with session_scope() as session:
        return [
            as_hypothesis_id(hypothesis_id)
            for hypothesis_id in session.scalars(
                select(HypothesisRow.hypothesis_id)
                .where(HypothesisRow.case_id == str(case_id))
                .order_by(HypothesisRow.last_updated_at.asc())
            ).all()
        ]


def top_confidence_score(case_id: CaseId) -> float:
    initialize()
    with session_scope() as session:
        confidence = session.scalar(
            select(func.max(HypothesisRow.confidence_score)).where(
                HypothesisRow.case_id == str(case_id)
            )
        )
        return float(confidence or 0.0)


def has_supported_hypothesis(case_id: CaseId) -> bool:
    initialize()
    with session_scope() as session:
        supported_id = session.scalar(
            select(HypothesisRow.hypothesis_id)
            .where(HypothesisRow.case_id == str(case_id))
            .where(HypothesisRow.status == HypothesisStatus.SUPPORTED.value)
            .limit(1)
        )
        return supported_id is not None


def highest_confidence_hypothesis(case_id: CaseId) -> HypothesisRow | None:
    initialize()
    with session_scope() as session:
        return session.scalars(
            select(HypothesisRow)
            .where(HypothesisRow.case_id == str(case_id))
            .order_by(HypothesisRow.confidence_score.desc(), HypothesisRow.last_updated_at.desc())
            .limit(1)
        ).first()


def get_hypothesis_state(case_id: CaseId, hypothesis_id: HypothesisId) -> HypothesisRow:
    initialize()
    with session_scope() as session:
        row = session.get(HypothesisRow, hypothesis_id)
        if row is None or row.case_id != str(case_id):
            raise KeyError(f"hypothesis not found: {hypothesis_id}")
        return row


def add_hypothesis_evidence_link(
    case_id: CaseId,
    hypothesis_id: HypothesisId,
    evidence_id: str,
    relation: str,
) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)

        hypothesis = session.get(HypothesisRow, hypothesis_id)
        if hypothesis is None or hypothesis.case_id != case_str:
            raise KeyError(f"hypothesis not found: {hypothesis_id}")

        evidence = session.get(EvidenceRecordRow, evidence_id)
        if evidence is None or evidence.case_id != case_str:
            raise KeyError(f"evidence not found: {evidence_id}")

        row = session.get(HypothesisEvidenceLinkRow, (hypothesis_id, evidence_id, relation))
        if row is None:
            session.add(
                HypothesisEvidenceLinkRow(
                    hypothesis_id=hypothesis_id,
                    evidence_id=evidence_id,
                    relation=relation,
                )
            )


def list_hypothesis_ids_for_evidence(
    case_id: CaseId,
    evidence_id: str,
) -> list[HypothesisId]:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        return [
            as_hypothesis_id(row.hypothesis_id)
            for row in session.scalars(
                select(HypothesisEvidenceLinkRow)
                .join(
                    HypothesisRow,
                    HypothesisRow.hypothesis_id == HypothesisEvidenceLinkRow.hypothesis_id,
                )
                .where(HypothesisEvidenceLinkRow.evidence_id == evidence_id)
                .where(HypothesisRow.case_id == case_str)
            ).all()
        ]


def _write_hypothesis_row(row: HypothesisRow, hypothesis: HypothesisRow) -> None:
    row.case_id = hypothesis.case_id
    row.statement = hypothesis.statement
    row.status = hypothesis.status
    row.confidence_score = hypothesis.confidence_score
    row.last_updated_at = hypothesis.last_updated_at
