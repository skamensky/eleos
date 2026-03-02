from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from eleos.db.engine import session_scope
from eleos.db.models import (
    CognitionEvidenceLinkRow,
    CognitionHypothesisLinkRow,
    CognitionRecordRow,
)
from eleos.db.state_support import initialize, lock_case_row
from eleos.models.enums import CognitionRecordType, DecisionAction
from eleos.models.ids import CaseId


def add_observation(
    *,
    case_id: CaseId,
    linked_hypothesis_ids: list[str],
    linked_evidence_ids: list[str],
) -> None:
    _add_record(
        case_id=case_id,
        record_type=CognitionRecordType.OBSERVATION,
        linked_hypothesis_ids=linked_hypothesis_ids,
        linked_evidence_ids=linked_evidence_ids,
    )


def add_decision(
    *,
    case_id: CaseId,
    linked_hypothesis_ids: list[str],
    linked_evidence_ids: list[str],
    action: DecisionAction,
    reason: str,
) -> None:
    _add_record(
        case_id=case_id,
        record_type=CognitionRecordType.DECISION,
        linked_hypothesis_ids=linked_hypothesis_ids,
        linked_evidence_ids=linked_evidence_ids,
        decision_action=action.value,
        decision_reason=reason,
    )


def add_feedback(
    *,
    case_id: CaseId,
    linked_hypothesis_ids: list[str],
    linked_evidence_ids: list[str],
    requires_replan: bool,
    reason: str,
    novelty_score: float,
    drift_score: float,
) -> None:
    _add_record(
        case_id=case_id,
        record_type=CognitionRecordType.FEEDBACK,
        linked_hypothesis_ids=linked_hypothesis_ids,
        linked_evidence_ids=linked_evidence_ids,
        feedback_requires_replan=requires_replan,
        feedback_reason=reason,
        feedback_novelty_score=novelty_score,
        feedback_drift_score=drift_score,
    )


def add_insight(
    *,
    case_id: CaseId,
    linked_hypothesis_ids: list[str],
    linked_evidence_ids: list[str],
    insight_text: str,
) -> None:
    _add_record(
        case_id=case_id,
        record_type=CognitionRecordType.INSIGHT,
        linked_hypothesis_ids=linked_hypothesis_ids,
        linked_evidence_ids=linked_evidence_ids,
        insight_text=insight_text,
    )


def _add_record(
    *,
    case_id: CaseId,
    record_type: CognitionRecordType,
    linked_hypothesis_ids: list[str],
    linked_evidence_ids: list[str],
    decision_action: str | None = None,
    decision_reason: str | None = None,
    feedback_requires_replan: bool | None = None,
    feedback_reason: str | None = None,
    feedback_novelty_score: float | None = None,
    feedback_drift_score: float | None = None,
    insight_text: str | None = None,
) -> None:
    initialize()
    case_str = str(case_id)
    record_id = str(uuid4())
    with session_scope() as session:
        lock_case_row(session, case_str)
        session.add(
            CognitionRecordRow(
                record_id=record_id,
                case_id=case_str,
                record_type=record_type.value,
                timestamp=datetime.now(timezone.utc),
                decision_action=decision_action,
                decision_reason=decision_reason,
                feedback_requires_replan=feedback_requires_replan,
                feedback_reason=feedback_reason,
                feedback_novelty_score=feedback_novelty_score,
                feedback_drift_score=feedback_drift_score,
                insight_text=insight_text,
            )
        )
        session.flush()

        for hypothesis_id in dict.fromkeys(linked_hypothesis_ids):
            session.add(
                CognitionHypothesisLinkRow(
                    record_id=record_id,
                    hypothesis_id=hypothesis_id,
                )
            )

        for evidence_id in dict.fromkeys(linked_evidence_ids):
            session.add(
                CognitionEvidenceLinkRow(
                    record_id=record_id,
                    evidence_id=evidence_id,
                )
            )
