from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

from eleos.models.case import InvestigationRequest
from eleos.models.enums import TerminationReason
from eleos.models.ids import CaseId
from eleos.models.report import FinalReport


class GraphNodeName(str, Enum):
    BOOTSTRAP_CASE = "bootstrap_case"
    EVALUATE_TERMINATION = "evaluate_termination"
    SELECT_TASK = "select_task"
    EXECUTE_TASK = "execute_task"
    UPDATE_REASONING = "update_reasoning"
    FINALIZE_CASE = "finalize_case"


class SelectionOutcome(str, Enum):
    SELECTED = "selected"
    NO_VALID_TASK = "no_valid_task"
    PRUNED_LOW_VALUE = "pruned_low_value"
    PRUNED_INVALID_LINK = "pruned_invalid_link"


class ExecutionOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    TOOL_FAILURE = "tool_failure"


class InvestigationGraphState(BaseModel):
    request: InvestigationRequest
    case_id: CaseId
    case_class: str | None = None
    playbook_id: str | None = None
    selected_task_id: str | None = None
    evidence_id: str | None = None
    should_stop: bool = False
    termination_reason: TerminationReason | None = None
    selection_outcome: SelectionOutcome | None = None
    execution_outcome: ExecutionOutcome | None = None
    final_report: FinalReport | None = None

    model_config = ConfigDict(frozen=True)

    # We intentionally avoid dict-based partial update helpers for graph transitions.
    # The update payload is typically typed as `Mapping[str, Any]`, which weakens static checks.
    # These helpers keep updates type-safe while avoiding repeated constructor
    # boilerplate in every node.
    def with_bootstrap(self, *, case_class: str, playbook_id: str) -> "InvestigationGraphState":
        return InvestigationGraphState(
            request=self.request,
            case_id=self.case_id,
            case_class=case_class,
            playbook_id=playbook_id,
            selected_task_id=None,
            evidence_id=None,
            should_stop=False,
            termination_reason=None,
            selection_outcome=None,
            execution_outcome=None,
            final_report=self.final_report,
        )

    def with_termination(
        self,
        *,
        should_stop: bool,
        termination_reason: TerminationReason,
    ) -> "InvestigationGraphState":
        return InvestigationGraphState(
            request=self.request,
            case_id=self.case_id,
            case_class=self.case_class,
            playbook_id=self.playbook_id,
            selected_task_id=self.selected_task_id,
            evidence_id=self.evidence_id,
            should_stop=should_stop,
            termination_reason=termination_reason,
            selection_outcome=self.selection_outcome,
            execution_outcome=self.execution_outcome,
            final_report=self.final_report,
        )

    def with_selection(
        self,
        *,
        selected_task_id: str | None,
        selection_outcome: SelectionOutcome,
    ) -> "InvestigationGraphState":
        return InvestigationGraphState(
            request=self.request,
            case_id=self.case_id,
            case_class=self.case_class,
            playbook_id=self.playbook_id,
            selected_task_id=selected_task_id,
            evidence_id=self.evidence_id,
            should_stop=self.should_stop,
            termination_reason=self.termination_reason,
            selection_outcome=selection_outcome,
            execution_outcome=self.execution_outcome,
            final_report=self.final_report,
        )

    def with_execution(
        self,
        *,
        execution_outcome: ExecutionOutcome,
        selected_task_id: str | None,
        evidence_id: str | None,
    ) -> "InvestigationGraphState":
        return InvestigationGraphState(
            request=self.request,
            case_id=self.case_id,
            case_class=self.case_class,
            playbook_id=self.playbook_id,
            selected_task_id=selected_task_id,
            evidence_id=evidence_id,
            should_stop=self.should_stop,
            termination_reason=self.termination_reason,
            selection_outcome=self.selection_outcome,
            execution_outcome=execution_outcome,
            final_report=self.final_report,
        )

    def without_evidence(self) -> "InvestigationGraphState":
        return InvestigationGraphState(
            request=self.request,
            case_id=self.case_id,
            case_class=self.case_class,
            playbook_id=self.playbook_id,
            selected_task_id=self.selected_task_id,
            evidence_id=None,
            should_stop=self.should_stop,
            termination_reason=self.termination_reason,
            selection_outcome=self.selection_outcome,
            execution_outcome=self.execution_outcome,
            final_report=self.final_report,
        )

    def with_final_report(self, report: FinalReport) -> "InvestigationGraphState":
        return InvestigationGraphState(
            request=self.request,
            case_id=self.case_id,
            case_class=self.case_class,
            playbook_id=self.playbook_id,
            selected_task_id=self.selected_task_id,
            evidence_id=self.evidence_id,
            should_stop=self.should_stop,
            termination_reason=self.termination_reason,
            selection_outcome=self.selection_outcome,
            execution_outcome=self.execution_outcome,
            final_report=report,
        )


def parse_graph_state(value: InvestigationGraphState | dict[str, Any]) -> InvestigationGraphState:
    return InvestigationGraphState.model_validate(value)
