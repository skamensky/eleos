from __future__ import annotations

from eleos.db import state_cases, state_evidence, state_hypotheses, state_tasks
from eleos.db.models import EvidenceRecordRow
from eleos.db.playbooks import resolve_latest_effective
from eleos.db.views.mappers import (
    to_evidence_view,
    to_hypothesis_view,
    to_mandatory_check_view,
    to_playbook_view,
    to_task_view,
)
from eleos.db.views.models import (
    EvidenceRecordView,
    FollowupTaskInputView,
    HypothesisSeedInputView,
    HypothesisUpdateInputView,
    RawDetailInputView,
    ReplanTaskInputView,
    TaskSeedInputView,
    TaskSelectionInputView,
)
from eleos.models.enums import Mode
from eleos.models.ids import CaseId


def build_hypothesis_seed_input(case_id: CaseId) -> HypothesisSeedInputView:
    case = state_cases.get_case_state(case_id)
    playbook = resolve_latest_effective(case_class=case.case_class)
    return HypothesisSeedInputView(
        case_id=case_id,
        objective=case.objective,
        mode=Mode(case.mode),
        case_class=case.case_class,
        playbook=to_playbook_view(playbook),
    )


def build_task_seed_input(case_id: CaseId) -> TaskSeedInputView:
    case = state_cases.get_case_state(case_id)
    playbook = resolve_latest_effective(case_class=case.case_class)
    hypotheses = [to_hypothesis_view(row) for row in state_hypotheses.list_hypotheses(case_id)]
    return TaskSeedInputView(
        case_id=case_id,
        objective=case.objective,
        mode=Mode(case.mode),
        case_class=case.case_class,
        playbook=to_playbook_view(playbook),
        hypotheses=hypotheses,
    )


def build_task_selection_input(
    case_id: CaseId,
    unresolved_check_ids: set[str],
    expected_value_floor: float,
) -> TaskSelectionInputView:
    case = state_cases.get_case_state(case_id)
    pending_tasks = [to_task_view(row) for row in state_tasks.list_pending_tasks(case_id)]
    unresolved_checks = [
        to_mandatory_check_view(row)
        for row in state_cases.list_mandatory_checks(case_id)
        if row.check_id in unresolved_check_ids
    ]
    return TaskSelectionInputView(
        objective=case.objective,
        mode=Mode(case.mode),
        pending_tasks=pending_tasks,
        unresolved_mandatory_checks=unresolved_checks,
        last_novelty_signal=case.last_novelty_signal,
        expected_value_floor=expected_value_floor,
    )


def build_hypothesis_update_input(case_id: CaseId) -> HypothesisUpdateInputView | None:
    evidence = state_evidence.latest_evidence(case_id)
    if evidence is None:
        return None
    hypotheses = [to_hypothesis_view(row) for row in state_hypotheses.list_hypotheses(case_id)]
    return HypothesisUpdateInputView(
        hypotheses=hypotheses,
        evidence=to_evidence_view(evidence),
    )


def build_followup_task_input(case_id: CaseId) -> FollowupTaskInputView | None:
    case = state_cases.get_case_state(case_id)
    evidence = state_evidence.latest_evidence(case_id)
    if evidence is None:
        return None
    all_evidence = state_evidence.list_evidence(case_id)
    prior_evidence = [row for row in all_evidence if row.evidence_id != evidence.evidence_id]
    hypotheses = [to_hypothesis_view(row) for row in state_hypotheses.list_hypotheses(case_id)]
    tasks = [to_task_view(row) for row in state_tasks.list_tasks(case_id)]
    return FollowupTaskInputView(
        objective=case.objective,
        mode=Mode(case.mode),
        hypotheses=hypotheses,
        tasks=tasks,
        evidence=to_evidence_view(evidence),
        recent_evidence_history=_bounded_recent_evidence_history(prior_evidence),
    )


def build_replan_task_input(case_id: CaseId, reason: str) -> ReplanTaskInputView:
    case = state_cases.get_case_state(case_id)
    hypotheses = [to_hypothesis_view(row) for row in state_hypotheses.list_hypotheses(case_id)]
    tasks = [to_task_view(row) for row in state_tasks.list_tasks(case_id)]
    return ReplanTaskInputView(
        objective=case.objective,
        mode=Mode(case.mode),
        reason=reason,
        hypotheses=hypotheses,
        tasks=tasks,
    )


def build_raw_detail_input(evidence_id: str) -> RawDetailInputView:
    evidence = state_evidence.get_evidence_record(evidence_id)
    return RawDetailInputView(evidence=to_evidence_view(evidence))


def _bounded_recent_evidence_history(
    prior_evidence: list[EvidenceRecordRow],
    *,
    max_items: int = 30,
    max_summary_bytes: int = 4000,
) -> list[EvidenceRecordView]:
    selected: list[EvidenceRecordView] = []
    used_summary_bytes = 0
    for row in reversed(prior_evidence):
        summary_bytes = len(row.finding_summary.encode("utf-8"))
        if len(selected) >= max_items:
            break
        if selected and used_summary_bytes + summary_bytes > max_summary_bytes:
            break
        view = to_evidence_view(row)
        selected.append(view)
        used_summary_bytes += summary_bytes
        if used_summary_bytes >= max_summary_bytes:
            break
    selected.reverse()
    return selected
