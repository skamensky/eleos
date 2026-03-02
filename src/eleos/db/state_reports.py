from __future__ import annotations

from sqlalchemy import delete

from eleos.db.engine import session_scope
from eleos.db.models import (
    CaseFinalReportCheckRow,
    CaseFinalReportEvidenceLinkRow,
    CaseFinalReportHypothesisLinkRow,
    CaseFinalReportRow,
    CaseRunRow,
)
from eleos.db.state_support import initialize, lock_case_row, now_utc
from eleos.models.enums import CaseStatus
from eleos.models.ids import CaseId
from eleos.models.report import FinalReport


def complete_case(case_id: CaseId, final_status: CaseStatus, report: FinalReport) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        case_row = session.get(CaseRunRow, case_str)
        if case_row is None:
            raise KeyError(f"case not found: {case_str}")
        case_row.status = final_status.value
        case_row.updated_at = now_utc()

        row = session.get(CaseFinalReportRow, case_str)
        if row is None:
            row = CaseFinalReportRow(
                case_id=case_str,
                objective=report.objective,
                final_assessment=report.final_assessment,
                confidence_score=report.confidence_score,
                confidence_label=report.confidence_label,
                completion_gate_passed=report.completion_gate_status.passed,
                customer_followups=list(report.customer_followups),
                internal_support_followups=list(report.internal_support_followups),
                escalation=report.escalation,
                termination_loop_count=report.termination_snapshot.loop_count,
            )
            session.add(row)
        else:
            row.objective = report.objective
            row.final_assessment = report.final_assessment
            row.confidence_score = report.confidence_score
            row.confidence_label = report.confidence_label
            row.completion_gate_passed = report.completion_gate_status.passed
            row.customer_followups = list(report.customer_followups)
            row.internal_support_followups = list(report.internal_support_followups)
            row.escalation = report.escalation
            row.termination_loop_count = report.termination_snapshot.loop_count
            row.updated_at = now_utc()

        session.execute(
            delete(CaseFinalReportCheckRow).where(CaseFinalReportCheckRow.case_id == case_str)
        )
        for check in report.completion_gate_status.checks:
            session.add(
                CaseFinalReportCheckRow(
                    case_id=case_str,
                    check_id=check.check_id,
                    description=check.description,
                    passed=check.passed,
                    reason=check.reason,
                )
            )

        session.execute(
            delete(CaseFinalReportEvidenceLinkRow).where(
                CaseFinalReportEvidenceLinkRow.case_id == case_str
            )
        )
        for evidence_id in dict.fromkeys(report.evidence_ledger_refs):
            session.add(
                CaseFinalReportEvidenceLinkRow(
                    case_id=case_str,
                    evidence_id=evidence_id,
                )
            )

        session.execute(
            delete(CaseFinalReportHypothesisLinkRow).where(
                CaseFinalReportHypothesisLinkRow.case_id == case_str
            )
        )
        for hypothesis in report.hypotheses_considered:
            session.add(
                CaseFinalReportHypothesisLinkRow(
                    case_id=case_str,
                    hypothesis_id=hypothesis.hypothesis_id,
                )
            )
