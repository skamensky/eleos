from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from eleos.graph.nodes import InvestigationGraphNodes
from eleos.graph.routes import (
    route_after_execute_task,
    route_after_select_task,
    route_after_termination,
)
from eleos.graph.state import GraphNodeName, InvestigationGraphState, parse_graph_state
from eleos.models.case import InvestigationRequest
from eleos.models.ids import CaseId


class InvestigationGraphApp:
    def __init__(self) -> None:
        self._nodes = InvestigationGraphNodes()

        workflow = StateGraph(cast(Any, InvestigationGraphState))
        workflow.add_node(GraphNodeName.BOOTSTRAP_CASE, self._nodes.bootstrap_case)
        workflow.add_node(GraphNodeName.EVALUATE_TERMINATION, self._nodes.evaluate_termination)
        workflow.add_node(GraphNodeName.SELECT_TASK, self._nodes.select_task)
        workflow.add_node(GraphNodeName.EXECUTE_TASK, self._nodes.execute_task)
        workflow.add_node(GraphNodeName.UPDATE_REASONING, self._nodes.update_reasoning)
        workflow.add_node(GraphNodeName.FINALIZE_CASE, self._nodes.finalize_case)

        workflow.add_edge(START, GraphNodeName.BOOTSTRAP_CASE)
        workflow.add_edge(GraphNodeName.BOOTSTRAP_CASE, GraphNodeName.EVALUATE_TERMINATION)
        workflow.add_conditional_edges(
            GraphNodeName.EVALUATE_TERMINATION,
            route_after_termination,
        )
        workflow.add_conditional_edges(
            GraphNodeName.SELECT_TASK,
            route_after_select_task,
        )
        workflow.add_conditional_edges(
            GraphNodeName.EXECUTE_TASK,
            route_after_execute_task,
        )
        workflow.add_edge(GraphNodeName.UPDATE_REASONING, GraphNodeName.EVALUATE_TERMINATION)
        workflow.add_edge(GraphNodeName.FINALIZE_CASE, END)
        self._graph: Any = workflow.compile(name="eleos_investigation")

    def invoke(self, request: InvestigationRequest, case_id: CaseId) -> InvestigationGraphState:
        initial_state = InvestigationGraphState(request=request, case_id=case_id)
        result = self._graph.invoke(
            initial_state,
            config=self._config_for(case_id),
        )
        return parse_graph_state(cast(dict[str, Any], result))

    def _config_for(self, case_id: CaseId) -> dict[str, Any]:
        return {"configurable": {"thread_id": str(case_id)}}


_graph_app: InvestigationGraphApp | None = None


def get_graph_app() -> InvestigationGraphApp:
    global _graph_app
    if _graph_app is None:
        _graph_app = InvestigationGraphApp()
    return _graph_app
