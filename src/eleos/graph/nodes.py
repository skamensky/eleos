from __future__ import annotations

from datetime import datetime, timezone

from eleos.core.cognition import (
    write_decision,
    write_feedback,
    write_insight,
    write_observation,
)
from eleos.core.context_transfer import summarize_evidence
from eleos.core.critic import evaluate_critic, reduce_critic_depth
from eleos.core.evidence_ledger import (
    attach_evidence_detail,
    get_evidence_raw,
    record,
)
from eleos.core.executor import finish_tool_execution, run_tool_plan, start_tool_execution
from eleos.core.planner import (
    apply_failure_action,
    choose_next_task,
    limit_to_serial_path,
    needs_raw_detail,
    replan,
    seed_hypotheses,
    seed_tasks,
    update_hypotheses,
    update_tasks,
)
from eleos.core.reporter import generate_report
from eleos.core.termination import evaluate_termination, unresolved_mandatory_checks
from eleos.db import (
    state_cases,
    state_evidence,
    state_hypotheses,
    state_reports,
    state_tasks,
    state_termination,
    state_tools,
)
from eleos.db.models import CaseMandatoryCheckRow, CaseRunRow, HypothesisRow, TaskRow
from eleos.db.playbooks import resolve_latest_effective
from eleos.graph.state import (
    ExecutionOutcome,
    InvestigationGraphState,
    SelectionOutcome,
)
from eleos.llm.agents.classifier.agent import classify_case
from eleos.logging.logger import get_logger
from eleos.models.agents.planner.models import TaskSelectionOutcome
from eleos.models.case import build_timeout
from eleos.models.enums import (
    CaseStatus,
    DecisionAction,
    EnforcementMode,
    LogEvent,
    Mode,
    TaskStatus,
    TerminationReason,
)
from eleos.models.ids import CaseId, as_hypothesis_id
from eleos.settings.config import config

logger = get_logger(__name__)


class InvestigationGraphNodes:
    def bootstrap_case(self, state: InvestigationGraphState) -> InvestigationGraphState:
        request = state.request
        case_id = state.case_id
        case_class = classify_case(request.objective)
        playbook = resolve_latest_effective(case_class=case_class)

        case_row = CaseRunRow(
            case_id=str(case_id),
            case_class=case_class,
            status=CaseStatus.RUNNING.value,
            objective=request.objective,
            mode=request.mode.value,
            playbook_policy=request.playbook_policy.value,
            timeout_at=build_timeout(request.timeout_minutes),
            completion_require_objective_satisfied=True,
            completion_require_evidence_completeness=True,
            completion_require_confidence_threshold=True,
            completion_allow_stop_on_timeout=True,
            request_source_channel=None,
            request_requester=None,
            request_tags=[],
            escalation_required=False,
            loop_count=0,
            last_novelty_signal=None,
            critic_depth_multiplier=1.0,
        )
        mandatory_checks = [
            CaseMandatoryCheckRow(
                case_id=str(case_id),
                check_id=step.step_id,
                description=step.completion_check,
                passed=None,
                reason=None,
            )
            for step in playbook.steps
            if step.required
        ]

        state_cases.register_case(case_row, mandatory_checks)
        seed_hypotheses(case_id)
        seed_tasks(case_id)
        logger.info(
            LogEvent.INVESTIGATION_INITIALIZED.value,
            case_id=case_id,
            case_class=case_class,
            mode=request.mode.value,
            playbook_id=playbook.playbook_id,
        )
        return state.with_bootstrap(case_class=case_class, playbook_id=playbook.playbook_id)

    def evaluate_termination(self, state: InvestigationGraphState) -> InvestigationGraphState:
        case_id = state.case_id
        case = state_cases.get_case_state(case_id)
        if case.loop_count >= config.runtime.max_iterations:
            case.escalation_required = True
            state_cases.save_case(case)

        termination_eval = evaluate_termination(case_id)
        state_termination.save_termination_snapshot(
            case_id=case_id,
            loop_count=case.loop_count,
            snapshot=termination_eval,
        )
        reason = TerminationReason(termination_eval.reason)
        logger.info(
            LogEvent.TERMINATION_SNAPSHOT.value,
            case_id=case_id,
            should_stop=termination_eval.should_stop,
            reason=reason.value,
            loop_count=case.loop_count,
        )
        return state.with_termination(
            should_stop=termination_eval.should_stop,
            termination_reason=reason,
        )

    def select_task(self, state: InvestigationGraphState) -> InvestigationGraphState:
        case_id = state.case_id
        case = state_cases.get_case_state(case_id)
        tasks = state_tasks.list_tasks(case_id)
        unresolved_checks = unresolved_mandatory_checks(case_id)
        next_task = self._force_required_task(
            case_id=case_id,
            unresolved_mandatory_checks=unresolved_checks,
        )
        selection_reason = "no valid next action"
        if next_task is None:
            selection_decision = choose_next_task(
                case_id=case_id,
                unresolved_mandatory_checks=unresolved_checks,
            )
            selection_reason = selection_decision.reason
            if selection_decision.outcome == TaskSelectionOutcome.SELECTED:
                if selection_decision.selected_task_id is None:
                    raise ValueError("task selection outcome was selected without task id")
                next_task = self._task_by_id(tasks, selection_decision.selected_task_id)
                if next_task is None:
                    raise ValueError("selected task was not found in current task set")
            elif selection_decision.outcome == TaskSelectionOutcome.PRUNED:
                if selection_decision.prune_task_id is None:
                    raise ValueError("task selection outcome was pruned without prune task id")
                prune_task = self._task_by_id(tasks, selection_decision.prune_task_id)
                if prune_task is None:
                    raise ValueError("pruned task was not found in current task set")
                pruned = self._mark_pruned(prune_task)
                state_tasks.save_tasks(case_id, self._update_task(tasks, pruned))
                write_decision(
                    case_id,
                    action=DecisionAction.PRUNE_TASK,
                    linked_evidence_id=None,
                    reason=selection_decision.reason,
                )
                case.loop_count += 1
                state_cases.save_case(case)
                return state.with_selection(
                    selected_task_id=None,
                    selection_outcome=SelectionOutcome.PRUNED_LOW_VALUE,
                )
        if next_task is None:
            write_decision(
                case_id,
                action=DecisionAction.REPLAN,
                linked_evidence_id=None,
                reason=selection_reason,
            )
            replan(case_id, reason="no_valid_next_action")
            case.loop_count += 1
            state_cases.save_case(case)
            return state.with_selection(
                selected_task_id=None,
                selection_outcome=SelectionOutcome.NO_VALID_TASK,
            )

        hypotheses = state_hypotheses.list_hypotheses(case_id)
        if not self._is_hypothesis_link_valid(next_task, hypotheses):
            pruned = self._mark_pruned(next_task)
            state_tasks.save_tasks(case_id, self._update_task(tasks, pruned))
            write_decision(
                case_id,
                action=DecisionAction.PRUNE_TASK,
                linked_evidence_id=None,
                reason="invalid_hypothesis_link",
            )
            case.loop_count += 1
            state_cases.save_case(case)
            return state.with_selection(
                selected_task_id=None,
                selection_outcome=SelectionOutcome.PRUNED_INVALID_LINK,
            )

        return state.with_selection(
            selected_task_id=next_task.task_id,
            selection_outcome=SelectionOutcome.SELECTED,
        )

    def execute_task(self, state: InvestigationGraphState) -> InvestigationGraphState:
        case_id = state.case_id
        selected_task_id = state.selected_task_id
        if selected_task_id is None:
            return state.with_execution(
                execution_outcome=ExecutionOutcome.TOOL_FAILURE,
                selected_task_id=None,
                evidence_id=state.evidence_id,
            )

        tasks = state_tasks.list_tasks(case_id)
        selected_task = self._task_by_id(tasks, selected_task_id)
        if selected_task is None:
            return state.with_execution(
                execution_outcome=ExecutionOutcome.TOOL_FAILURE,
                selected_task_id=None,
                evidence_id=state.evidence_id,
            )

        in_progress = self._mark_in_progress(selected_task)
        state_tasks.save_tasks(case_id, self._update_task(tasks, in_progress))
        tool_execution = start_tool_execution(in_progress)
        state_tools.save_tool_execution(case_id, tool_execution)
        result = run_tool_plan(in_progress)
        tool_execution = finish_tool_execution(tool_execution, result)
        state_tools.save_tool_execution(case_id, tool_execution)

        if result.failed:
            failed = self._mark_failed(in_progress)
            state_tasks.save_tasks(case_id, self._update_task(tasks, failed))
            apply_failure_action(case_id, failed)
            write_decision(
                case_id,
                action=DecisionAction.TOOL_FAILURE,
                linked_evidence_id=None,
                reason=result.error or "tool execution failed",
            )
            case = state_cases.get_case_state(case_id)
            case.loop_count += 1
            state_cases.save_case(case)
            return state.with_execution(
                execution_outcome=ExecutionOutcome.TOOL_FAILURE,
                selected_task_id=None,
                evidence_id=state.evidence_id,
            )

        evidence = record(
            case_id=case_id,
            result=result,
            tool_execution=tool_execution,
            linked_hypothesis_id=(
                as_hypothesis_id(in_progress.linked_hypothesis_id)
                if in_progress.linked_hypothesis_id is not None
                else None
            ),
        )
        evidence = summarize_evidence(evidence)
        tasks = state_tasks.list_tasks(case_id)
        done_task = self._mark_done(in_progress, evidence.evidence_id)
        state_tasks.save_tasks(case_id, self._update_task(tasks, done_task))
        state_tasks.add_task_evidence_ref(case_id, done_task.task_id, evidence.evidence_id)
        write_observation(
            case_id,
            evidence,
            (
                as_hypothesis_id(in_progress.linked_hypothesis_id)
                if in_progress.linked_hypothesis_id is not None
                else None
            ),
        )

        if needs_raw_detail(evidence.evidence_id):
            raw_payload = get_evidence_raw(evidence.tool_execution_id)
            evidence = attach_evidence_detail(
                evidence_id=evidence.evidence_id,
                raw_payload=raw_payload,
                reason="summary_insufficient_or_high_impact",
            )
            logger.info(
                LogEvent.EVIDENCE_DETAIL_LOGGED.value,
                case_id=case_id,
                evidence_id=evidence.evidence_id,
            )

        return state.with_execution(
            execution_outcome=ExecutionOutcome.SUCCEEDED,
            selected_task_id=None,
            evidence_id=evidence.evidence_id,
        )

    def update_reasoning(self, state: InvestigationGraphState) -> InvestigationGraphState:
        case_id = state.case_id
        evidence_id = state.evidence_id
        if evidence_id is None:
            return state

        update_hypotheses(case_id)
        write_decision(
            case_id,
            action=DecisionAction.HYPOTHESIS_UPDATE,
            linked_evidence_id=evidence_id,
            reason="evidence_applied",
        )
        update_tasks(case_id)

        critic_assessment = evaluate_critic(case_id)
        write_feedback(case_id, critic_assessment)
        if critic_assessment.requires_replan:
            replan(case_id, reason=critic_assessment.reason)

        case = state_cases.get_case_state(case_id)
        if case.mode == Mode.FAST_MODE.value:
            reduce_critic_depth(case_id)
            limit_to_serial_path(case_id)

        case = state_cases.get_case_state(case_id)
        case.loop_count += 1
        evidence = state_evidence.get_evidence_record(evidence_id)
        case.last_novelty_signal = evidence.novelty_signal
        state_cases.save_case(case)
        return state.without_evidence()

    def finalize_case(self, state: InvestigationGraphState) -> InvestigationGraphState:
        case_id = state.case_id
        termination_reason = state.termination_reason or TerminationReason.CONTINUE
        report = generate_report(case_id)
        write_insight(
            case_id,
            text="Investigation closed with composable termination criteria",
        )
        state_reports.complete_case(
            case_id=case_id,
            final_status=self._resolve_final_status(termination_reason),
            report=report,
        )
        return state.with_final_report(report)

    def _is_hypothesis_link_valid(
        self,
        task: TaskRow,
        hypotheses: list[HypothesisRow],
    ) -> bool:
        if task.linked_hypothesis_id is None:
            return True
        hypothesis_ids = {hypothesis.hypothesis_id for hypothesis in hypotheses}
        return task.linked_hypothesis_id in hypothesis_ids

    def _task_by_id(self, tasks: list[TaskRow], task_id: str) -> TaskRow | None:
        for task in tasks:
            if task.task_id == task_id:
                return task
        return None

    def _update_task(self, tasks: list[TaskRow], updated_task: TaskRow) -> list[TaskRow]:
        return [updated_task if task.task_id == updated_task.task_id else task for task in tasks]

    def _mark_pruned(self, task: TaskRow) -> TaskRow:
        return self._task_with_status(task, TaskStatus.PRUNED)

    def _mark_failed(self, task: TaskRow) -> TaskRow:
        return self._task_with_status(task, TaskStatus.FAILED)

    def _mark_in_progress(self, task: TaskRow) -> TaskRow:
        return self._task_with_status(task, TaskStatus.IN_PROGRESS)

    def _mark_done(self, task: TaskRow, _evidence_ref: str) -> TaskRow:
        return self._task_with_status(task, TaskStatus.DONE)

    def _resolve_final_status(self, termination_reason: TerminationReason) -> CaseStatus:
        if termination_reason == TerminationReason.COMPLETION_CONDITIONS_MET:
            return CaseStatus.COMPLETED
        if termination_reason == TerminationReason.TIMEOUT_REACHED:
            return CaseStatus.TIMED_OUT
        if termination_reason == TerminationReason.ESCALATION_REQUIRED:
            return CaseStatus.ESCALATED
        if termination_reason == TerminationReason.EXPLORATION_EXHAUSTED:
            return CaseStatus.EXHAUSTED
        return CaseStatus.STOPPED

    def _force_required_task(
        self,
        case_id: CaseId,
        unresolved_mandatory_checks: list[CaseMandatoryCheckRow],
    ) -> TaskRow | None:
        case = state_cases.get_case_state(case_id)
        if case.playbook_policy != EnforcementMode.MANDATORY.value:
            return None
        if not unresolved_mandatory_checks:
            return None

        required_step_ids = {check.check_id for check in unresolved_mandatory_checks}
        forced = state_tasks.list_forced_pending_tasks(case_id, required_step_ids)
        if not forced:
            return None
        return forced[0]

    def _task_with_status(self, task: TaskRow, status: TaskStatus) -> TaskRow:
        task.status = status.value
        task.updated_at = datetime.now(timezone.utc)
        return task
