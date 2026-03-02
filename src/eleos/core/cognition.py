from __future__ import annotations

from eleos.db import state_cognition
from eleos.db.models import EvidenceRecordRow
from eleos.models.agents.critic.models import CriticAssessment
from eleos.models.enums import DecisionAction
from eleos.models.ids import CaseId, HypothesisId


def write_observation(
    case_id: CaseId,
    evidence: EvidenceRecordRow,
    linked_hypothesis_id: HypothesisId | None,
) -> None:
    linked_hypothesis_ids = [linked_hypothesis_id] if linked_hypothesis_id else []
    state_cognition.add_observation(
        case_id=case_id,
        linked_hypothesis_ids=linked_hypothesis_ids,
        linked_evidence_ids=[evidence.evidence_id],
    )


def write_decision(
    case_id: CaseId,
    action: DecisionAction,
    linked_evidence_id: str | None,
    reason: str,
) -> None:
    linked_evidence_ids = [linked_evidence_id] if linked_evidence_id else []
    state_cognition.add_decision(
        case_id=case_id,
        linked_hypothesis_ids=[],
        linked_evidence_ids=linked_evidence_ids,
        action=action,
        reason=reason,
    )


def write_feedback(case_id: CaseId, feedback: CriticAssessment) -> None:
    state_cognition.add_feedback(
        case_id=case_id,
        linked_hypothesis_ids=[],
        linked_evidence_ids=[],
        requires_replan=feedback.requires_replan,
        reason=feedback.reason,
        novelty_score=feedback.novelty_score,
        drift_score=feedback.drift_score,
    )


def write_insight(case_id: CaseId, text: str) -> None:
    state_cognition.add_insight(
        case_id=case_id,
        linked_hypothesis_ids=[],
        linked_evidence_ids=[],
        insight_text=text,
    )
