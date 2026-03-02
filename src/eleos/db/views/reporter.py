from __future__ import annotations

from eleos.db import state_cases, state_evidence, state_hypotheses
from eleos.db.models import TerminationSnapshotRow
from eleos.db.views.mappers import (
    to_evidence_view,
    to_hypothesis_view,
    to_termination_snapshot_view,
)
from eleos.db.views.models import ReportSynthesisInputView
from eleos.models.ids import CaseId
from eleos.models.report import CompletionGateStatus


def build_report_synthesis_input(
    case_id: CaseId,
    termination_snapshot: TerminationSnapshotRow,
    completion_gate_status: CompletionGateStatus,
) -> ReportSynthesisInputView:
    case = state_cases.get_case_state(case_id)
    hypotheses = [to_hypothesis_view(row) for row in state_hypotheses.list_hypotheses(case_id)]
    evidence = [to_evidence_view(row) for row in state_evidence.list_evidence(case_id)]
    return ReportSynthesisInputView(
        objective=case.objective,
        hypotheses=hypotheses,
        evidence_records=evidence,
        termination_snapshot=to_termination_snapshot_view(termination_snapshot),
        completion_gate_status=completion_gate_status,
    )
