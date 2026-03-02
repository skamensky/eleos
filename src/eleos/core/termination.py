from __future__ import annotations

from datetime import datetime, timezone

from eleos.db import state_cases, state_evidence, state_hypotheses, state_tasks
from eleos.db.models import CaseMandatoryCheckRow, TerminationSnapshotRow
from eleos.db.views.completion_checks import list_completion_check_inputs
from eleos.db.views.models import CompletionCheckInputView
from eleos.llm.agents.base.structured_agent import StructuredAgent
from eleos.llm.agents.termination.agent import completion_check_agent
from eleos.models.agents.termination.models import CompletionCheckDecision
from eleos.models.enums import TerminationReason
from eleos.models.ids import CaseId
from eleos.models.report import CompletionCheckStatus, CompletionGateStatus
from eleos.settings.config import config

_completion_check_agent: StructuredAgent[
    CompletionCheckInputView,
    CompletionCheckDecision,
] = completion_check_agent


def evaluate_termination(case_id: CaseId) -> TerminationSnapshotRow:
    case = state_cases.get_case_state(case_id)
    top_confidence = state_hypotheses.top_confidence_score(case_id)
    objective_satisfied = state_hypotheses.has_supported_hypothesis(case_id)
    evidence_completeness_sufficient = state_evidence.has_evidence(case_id)
    confidence_sufficient = top_confidence >= config.runtime.thresholds.confidence_sufficient
    timeout_reached = datetime.now(timezone.utc) >= case.timeout_at
    no_novel_signal = (
        (case.last_novelty_signal or 0.0)
        < config.runtime.thresholds.no_novelty_floor
    )
    expected_value_below_threshold = not state_tasks.has_pending_task_with_expected_value_at_least(
        case_id=case_id,
        expected_value_floor=config.runtime.thresholds.expected_value_floor,
    )
    escalation_required = case.escalation_required

    should_stop = False
    reason = TerminationReason.CONTINUE
    if timeout_reached:
        should_stop = True
        reason = TerminationReason.TIMEOUT_REACHED
    elif escalation_required:
        should_stop = True
        reason = TerminationReason.ESCALATION_REQUIRED
    elif objective_satisfied and evidence_completeness_sufficient and confidence_sufficient:
        should_stop = True
        reason = TerminationReason.COMPLETION_CONDITIONS_MET
    elif no_novel_signal and expected_value_below_threshold:
        should_stop = True
        reason = TerminationReason.EXPLORATION_EXHAUSTED

    return TerminationSnapshotRow(
        case_id=str(case_id),
        loop_count=case.loop_count,
        objective_satisfied=objective_satisfied,
        evidence_completeness_sufficient=evidence_completeness_sufficient,
        confidence_sufficient=confidence_sufficient,
        timeout_reached=timeout_reached,
        no_novel_signal=no_novel_signal,
        expected_value_below_threshold=expected_value_below_threshold,
        escalation_required=escalation_required,
        should_stop=should_stop,
        reason=reason.value,
    )


def evaluate_completion_gate(case_id: CaseId) -> CompletionGateStatus:
    check_inputs = list_completion_check_inputs(case_id)
    statuses = [_evaluate_check(check_input) for check_input in check_inputs]
    return CompletionGateStatus(passed=all(item.passed for item in statuses), checks=statuses)


def unresolved_mandatory_checks(case_id: CaseId) -> list[CaseMandatoryCheckRow]:
    mandatory_checks = state_cases.list_mandatory_checks(case_id)
    check_inputs = list_completion_check_inputs(case_id)
    statuses_by_check_id = {
        status.check_id: status
        for status in map(_evaluate_check, check_inputs)
    }
    return [
        check
        for check in mandatory_checks
        if not statuses_by_check_id.get(
            check.check_id,
            CompletionCheckStatus(
                check_id=check.check_id,
                description=check.description,
                passed=False,
                reason="check_not_evaluated",
            ),
        ).passed
    ]


def _evaluate_check(
    payload: CompletionCheckInputView,
) -> CompletionCheckStatus:
    decision = _completion_check_agent.run(payload)
    return CompletionCheckStatus(
        check_id=payload.check.check_id,
        description=payload.check.description,
        passed=decision.passed,
        reason=decision.reason,
    )
