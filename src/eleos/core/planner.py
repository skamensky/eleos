from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from eleos.db import state_cases, state_hypotheses, state_tasks
from eleos.db.models import CaseMandatoryCheckRow, HypothesisRow, TaskRow
from eleos.db.views.models import (
    CategoryToolGuidanceView,
    FollowupTaskInputView,
    HypothesisSeedInputView,
    HypothesisUpdateInputView,
    HypothesisView,
    RawDetailInputView,
    ReplanTaskInputView,
    TaskSeedInputView,
    TaskSelectionInputView,
)
from eleos.db.views.planner import (
    build_followup_task_input,
    build_hypothesis_seed_input,
    build_hypothesis_update_input,
    build_raw_detail_input,
    build_replan_task_input,
    build_task_seed_input,
    build_task_selection_input,
)
from eleos.llm.agents.base.structured_agent import StructuredAgent
from eleos.llm.agents.planner.agent import (
    followup_task_agent,
    hypothesis_seed_agent,
    hypothesis_update_agent,
    raw_detail_agent,
    replan_task_agent,
    task_seed_agent,
    task_selection_agent,
)
from eleos.models.agents.planner.models import (
    FollowupTaskOutput,
    HypothesisSeedOutput,
    HypothesisUpdateOutput,
    RawDetailDecision,
    ReplanTaskOutput,
    TaskSeedOutput,
    TaskSelectionDecision,
)
from eleos.models.enums import TaskStatus
from eleos.models.ids import CaseId, HypothesisId, as_hypothesis_id
from eleos.settings.config import config

_hypothesis_seed_agent: StructuredAgent[HypothesisSeedInputView, HypothesisSeedOutput] = (
    hypothesis_seed_agent
)
_task_seed_agent: StructuredAgent[TaskSeedInputView, TaskSeedOutput] = task_seed_agent
_hypothesis_update_agent: StructuredAgent[HypothesisUpdateInputView, HypothesisUpdateOutput] = (
    hypothesis_update_agent
)
_followup_task_agent: StructuredAgent[FollowupTaskInputView, FollowupTaskOutput] = (
    followup_task_agent
)
_replan_task_agent: StructuredAgent[ReplanTaskInputView, ReplanTaskOutput] = replan_task_agent
_raw_detail_agent: StructuredAgent[RawDetailInputView, RawDetailDecision] = raw_detail_agent
_task_selection_agent: StructuredAgent[TaskSelectionInputView, TaskSelectionDecision] = (
    task_selection_agent
)


def seed_hypotheses(case_id: CaseId) -> None:
    payload: HypothesisSeedInputView = build_hypothesis_seed_input(case_id)
    seeded = _hypothesis_seed_agent.run(payload).hypotheses
    if not seeded:
        raise ValueError("planner returned no initial hypotheses")

    now = datetime.now(timezone.utc)
    hypotheses: list[HypothesisRow] = []
    for hypothesis in seeded:
        hypothesis_id = _case_scoped_hypothesis_id(case_id, str(hypothesis.hypothesis_id))
        hypotheses.append(
            HypothesisRow(
                hypothesis_id=hypothesis_id,
                case_id=str(case_id),
                statement=hypothesis.statement,
                status=hypothesis.status.value,
                confidence_score=hypothesis.confidence_score,
                last_updated_at=now,
            )
        )
    state_hypotheses.save_hypotheses(case_id, hypotheses)


def seed_tasks(case_id: CaseId) -> None:
    seed_payload: TaskSeedInputView = build_task_seed_input(case_id)
    seeded_tasks = _task_seed_agent.run(seed_payload).tasks
    draft_by_step = {item.step_id: item for item in seeded_tasks}

    now = datetime.now(timezone.utc)
    tasks: list[TaskRow] = []
    for index, step in enumerate(seed_payload.playbook.steps, start=1):
        draft = draft_by_step.get(step.step_id)
        if draft is None:
            raise ValueError(f"planner missing task draft for step: {step.step_id}")
        linked_hypothesis_id = _resolve_linked_hypothesis_id(
            draft.linked_hypothesis_id,
            seed_payload.hypotheses,
        )
        task = TaskRow(
            task_id=str(uuid4()),
            case_id=str(case_id),
            linked_hypothesis_id=str(linked_hypothesis_id) if linked_hypothesis_id else None,
            intent=draft.intent,
            expected_evidence=draft.expected_evidence,
            expected_information_gain=draft.expected_information_gain,
            expected_value=draft.expected_value,
            tool_name=step.tool_selector,
            tool_input_objective=seed_payload.objective,
            tool_input_step=step.step_id,
            tool_input_reason=None,
            tool_input_evidence_id=None,
            status=TaskStatus.PENDING.value,
            priority=index,
            created_reason=step.step_id,
            updated_at=now,
        )
        tasks.append(task)

    if not tasks:
        raise ValueError("planner returned no initial tasks")
    state_tasks.save_tasks(case_id, tasks)
    hypothesis_ids = state_hypotheses.list_hypothesis_ids(case_id)
    for task in tasks:
        state_tasks.set_task_hypothesis_links(case_id, task.task_id, hypothesis_ids)


def choose_next_task(
    case_id: CaseId,
    unresolved_mandatory_checks: list[CaseMandatoryCheckRow],
) -> TaskSelectionDecision:
    unresolved_ids = {check.check_id for check in unresolved_mandatory_checks}
    payload: TaskSelectionInputView = build_task_selection_input(
        case_id=case_id,
        unresolved_check_ids=unresolved_ids,
        expected_value_floor=config.runtime.thresholds.expected_value_floor,
    )
    decision = _task_selection_agent.run(payload)
    pending_ids = {task.task_id for task in payload.pending_tasks}
    if decision.selected_task_id is not None and decision.selected_task_id not in pending_ids:
        raise ValueError("planner selected a task that is not pending")
    if decision.prune_task_id is not None and decision.prune_task_id not in pending_ids:
        raise ValueError("planner selected a prune target that is not pending")
    return decision


def update_hypotheses(case_id: CaseId) -> None:
    hypotheses = state_hypotheses.list_hypotheses(case_id)
    payload: HypothesisUpdateInputView | None = build_hypothesis_update_input(case_id)
    if payload is None:
        return

    decision = _hypothesis_update_agent.run(payload)
    assessments_by_id = {item.hypothesis_id: item for item in decision.assessments}

    now = datetime.now(timezone.utc)
    for hypothesis in hypotheses:
        hypothesis_id = as_hypothesis_id(hypothesis.hypothesis_id)
        assessment = assessments_by_id.get(hypothesis_id)
        if assessment is None:
            continue
        if assessment.supports_evidence:
            state_hypotheses.add_hypothesis_evidence_link(
                case_id=case_id,
                hypothesis_id=hypothesis_id,
                evidence_id=payload.evidence.evidence_id,
                relation="supports",
            )
        if assessment.contradicts_evidence:
            state_hypotheses.add_hypothesis_evidence_link(
                case_id=case_id,
                hypothesis_id=hypothesis_id,
                evidence_id=payload.evidence.evidence_id,
                relation="contradicts",
            )
        hypothesis.status = assessment.status.value
        hypothesis.confidence_score = assessment.confidence_score
        hypothesis.last_updated_at = now

    state_hypotheses.save_hypotheses(case_id, hypotheses)


def update_tasks(case_id: CaseId) -> None:
    tasks = state_tasks.list_tasks(case_id)
    base_payload: FollowupTaskInputView | None = build_followup_task_input(case_id)
    if base_payload is None:
        return

    if state_tasks.has_pending_tasks(case_id):
        return

    case_class = state_cases.get_case_state(case_id).case_class
    payload = FollowupTaskInputView(
        objective=base_payload.objective,
        mode=base_payload.mode,
        category_tools=_category_tool_guidance(case_class),
        hypotheses=base_payload.hypotheses,
        tasks=base_payload.tasks,
        evidence=base_payload.evidence,
        recent_evidence_history=base_payload.recent_evidence_history,
    )
    decision = _followup_task_agent.run(payload)
    if not decision.should_create:
        return

    if (
        decision.intent is None
        or decision.expected_evidence is None
        or decision.expected_information_gain is None
        or decision.expected_value is None
        or decision.tool_name is None
    ):
        raise ValueError("planner follow-up decision missing required task fields")

    linked_hypothesis_id = _resolve_linked_hypothesis_id(
        decision.linked_hypothesis_id,
        payload.hypotheses,
    )
    max_priority = state_tasks.max_task_priority(case_id)
    followup = TaskRow(
        task_id=str(uuid4()),
        case_id=str(case_id),
        linked_hypothesis_id=str(linked_hypothesis_id) if linked_hypothesis_id else None,
        intent=decision.intent,
        expected_evidence=decision.expected_evidence,
        expected_information_gain=decision.expected_information_gain,
        expected_value=decision.expected_value,
        tool_name=decision.tool_name,
        tool_input_objective=payload.objective,
        tool_input_step=None,
        tool_input_reason=None,
        tool_input_evidence_id=payload.evidence.evidence_id,
        status=TaskStatus.PENDING.value,
        priority=max_priority + 1,
        created_reason=f"followup-from-{payload.evidence.evidence_id}",
        updated_at=datetime.now(timezone.utc),
    )
    state_tasks.save_tasks(case_id, [*tasks, followup])
    if linked_hypothesis_id is not None:
        state_tasks.set_task_hypothesis_links(case_id, followup.task_id, [linked_hypothesis_id])


def apply_failure_action(
    case_id: CaseId,
    failed_task: TaskRow,
) -> None:
    tasks = state_tasks.list_tasks(case_id)
    retry_task = TaskRow(
        task_id=str(uuid4()),
        case_id=str(case_id),
        linked_hypothesis_id=failed_task.linked_hypothesis_id,
        intent=failed_task.intent,
        expected_evidence=failed_task.expected_evidence,
        expected_information_gain=failed_task.expected_information_gain,
        expected_value=failed_task.expected_value,
        tool_name=failed_task.tool_name,
        tool_input_objective=failed_task.tool_input_objective,
        tool_input_step=failed_task.tool_input_step,
        tool_input_reason=failed_task.tool_input_reason,
        tool_input_evidence_id=failed_task.tool_input_evidence_id,
        status=TaskStatus.PENDING.value,
        priority=failed_task.priority + 1,
        created_reason=f"retry-{failed_task.task_id}",
        updated_at=datetime.now(timezone.utc),
    )
    state_tasks.save_tasks(case_id, [*tasks, retry_task])
    state_tasks.copy_task_hypothesis_links(case_id, failed_task.task_id, retry_task.task_id)


def replan(
    case_id: CaseId,
    reason: str,
) -> None:
    tasks = state_tasks.list_tasks(case_id)
    if state_tasks.has_pending_tasks(case_id):
        return

    base_payload: ReplanTaskInputView = build_replan_task_input(case_id, reason)
    case_class = state_cases.get_case_state(case_id).case_class
    payload = ReplanTaskInputView(
        objective=base_payload.objective,
        mode=base_payload.mode,
        category_tools=_category_tool_guidance(case_class),
        reason=base_payload.reason,
        hypotheses=base_payload.hypotheses,
        tasks=base_payload.tasks,
    )
    decision = _replan_task_agent.run(payload)
    hypothesis_id = _resolve_linked_hypothesis_id(
        decision.linked_hypothesis_id,
        payload.hypotheses,
    )
    max_priority = state_tasks.max_task_priority(case_id)
    replanned = TaskRow(
        task_id=str(uuid4()),
        case_id=str(case_id),
        linked_hypothesis_id=str(hypothesis_id) if hypothesis_id else None,
        intent=decision.intent,
        expected_evidence=decision.expected_evidence,
        expected_information_gain=decision.expected_information_gain,
        expected_value=decision.expected_value,
        tool_name=decision.tool_name,
        tool_input_objective=payload.objective,
        tool_input_step=None,
        tool_input_reason=reason,
        tool_input_evidence_id=None,
        status=TaskStatus.PENDING.value,
        priority=max_priority + 1,
        created_reason=f"replan:{reason}",
        updated_at=datetime.now(timezone.utc),
    )
    state_tasks.save_tasks(case_id, [*tasks, replanned])
    if hypothesis_id is not None:
        state_tasks.set_task_hypothesis_links(case_id, replanned.task_id, [hypothesis_id])


def limit_to_serial_path(case_id: CaseId) -> None:
    tasks = state_tasks.list_tasks(case_id)

    pending = state_tasks.list_pending_tasks(case_id)
    if len(pending) <= 1:
        return

    first = pending[0].task_id
    updated: list[TaskRow] = []
    for task in tasks:
        if task.status == TaskStatus.PENDING.value and task.task_id != first:
            updated.append(_task_with_status(task, TaskStatus.PRUNED))
        else:
            updated.append(task)
    state_tasks.save_tasks(case_id, updated)


def needs_raw_detail(
    evidence_id: str,
) -> bool:
    payload: RawDetailInputView = build_raw_detail_input(evidence_id)
    decision = _raw_detail_agent.run(payload)
    return decision.needs_raw_detail


def _resolve_linked_hypothesis_id(
    candidate: HypothesisId | None,
    hypotheses: list[HypothesisView],
) -> HypothesisId | None:
    if candidate is None:
        return hypotheses[0].hypothesis_id if hypotheses else None
    hypothesis_ids = {hypothesis.hypothesis_id for hypothesis in hypotheses}
    if candidate in hypothesis_ids:
        return candidate
    return hypotheses[0].hypothesis_id if hypotheses else None


def _case_scoped_hypothesis_id(case_id: CaseId, raw_hypothesis_id: str) -> str:
    if raw_hypothesis_id.startswith(f"{case_id}:"):
        return raw_hypothesis_id
    return f"{case_id}:{raw_hypothesis_id}"


def _category_tool_guidance(case_class: str) -> CategoryToolGuidanceView:
    for category in config.classification.categories:
        if category.category_id == case_class:
            return CategoryToolGuidanceView(
                required_tool_references=list(category.required_tool_references),
                suggested_tool_references=list(category.suggested_tool_references),
            )
    raise LookupError(f"missing classification config for case class '{case_class}'")


def _task_with_status(task: TaskRow, status: TaskStatus) -> TaskRow:
    task.status = status.value
    task.updated_at = datetime.now(timezone.utc)
    return task
