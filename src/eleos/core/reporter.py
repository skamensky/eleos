from __future__ import annotations

from eleos.core.termination import evaluate_completion_gate, evaluate_termination
from eleos.db import state_cases, state_evidence, state_hypotheses, state_termination
from eleos.db.views.models import ReportSynthesisInputView
from eleos.db.views.reporter import build_report_synthesis_input
from eleos.llm.agents.base.structured_agent import StructuredAgent
from eleos.llm.agents.reporter.agent import report_synthesis_agent
from eleos.models.agents.reporter.models import ReportSynthesisOutput
from eleos.models.ids import CaseId
from eleos.models.report import FinalReport

_report_agent: StructuredAgent[
    ReportSynthesisInputView,
    ReportSynthesisOutput,
] = report_synthesis_agent


def generate_report(case_id: CaseId) -> FinalReport:
    case = state_cases.get_case_state(case_id)
    hypotheses = state_hypotheses.list_hypotheses(case_id)
    termination_snapshot = state_termination.latest_termination_snapshot(case_id)
    if termination_snapshot is None:
        termination_snapshot = evaluate_termination(case_id)

    if not hypotheses:
        raise ValueError("report generation requires at least one hypothesis")

    top_hypothesis = state_hypotheses.highest_confidence_hypothesis(case_id)
    if top_hypothesis is None:
        raise ValueError("report generation requires at least one hypothesis")
    confidence_score = top_hypothesis.confidence_score

    completion_gate_status = evaluate_completion_gate(case_id)
    payload: ReportSynthesisInputView = build_report_synthesis_input(
        case_id=case_id,
        termination_snapshot=termination_snapshot,
        completion_gate_status=completion_gate_status,
    )
    synthesis = _report_agent.run(payload)

    return FinalReport(
        objective=case.objective,
        final_assessment=synthesis.final_assessment,
        hypotheses_considered=hypotheses,
        evidence_ledger_refs=state_evidence.list_evidence_ids(case_id),
        confidence_score=confidence_score,
        confidence_label=synthesis.confidence_label,
        completion_gate_status=completion_gate_status,
        citations=state_evidence.list_evidence_tool_execution_ids(case_id),
        escalation=synthesis.escalation,
        customer_followups=synthesis.customer_followups,
        internal_support_followups=synthesis.internal_support_followups,
        termination_snapshot=termination_snapshot,
    )
