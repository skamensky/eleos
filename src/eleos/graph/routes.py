from __future__ import annotations

from eleos.graph.state import (
    ExecutionOutcome,
    GraphNodeName,
    InvestigationGraphState,
    SelectionOutcome,
)


def route_after_termination(state: InvestigationGraphState) -> GraphNodeName:
    if state.should_stop:
        return GraphNodeName.FINALIZE_CASE
    return GraphNodeName.SELECT_TASK


def route_after_select_task(state: InvestigationGraphState) -> GraphNodeName:
    if state.selection_outcome == SelectionOutcome.SELECTED:
        return GraphNodeName.EXECUTE_TASK
    return GraphNodeName.EVALUATE_TERMINATION


def route_after_execute_task(state: InvestigationGraphState) -> GraphNodeName:
    if state.execution_outcome == ExecutionOutcome.SUCCEEDED:
        return GraphNodeName.UPDATE_REASONING
    return GraphNodeName.EVALUATE_TERMINATION
