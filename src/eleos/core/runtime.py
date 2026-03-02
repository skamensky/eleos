from __future__ import annotations

from eleos.graph.app import InvestigationGraphApp, get_graph_app
from eleos.models.case import InvestigationRequest
from eleos.models.ids import CaseId, new_case_id
from eleos.models.report import FinalReport


class InvestigationRuntime:
    def __init__(self) -> None:
        self.graph_app: InvestigationGraphApp = get_graph_app()

    def run_with_case_id(self, request: InvestigationRequest) -> tuple[CaseId, FinalReport]:
        case_id = new_case_id()
        state = self.graph_app.invoke(request=request, case_id=case_id)
        report = state.final_report
        if report is None:
            raise RuntimeError("graph completed without final_report")
        return case_id, report

    def run(self, request: InvestigationRequest) -> FinalReport:
        _, report = self.run_with_case_id(request)
        return report
