from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from eleos.db.engine import session_scope
from eleos.db.models import CaseMandatoryCheckRow, CaseRunRow
from eleos.db.state_support import initialize, lock_case_row, now_utc
from eleos.models.enums import CaseStatus
from eleos.models.ids import CaseId


def register_case(case: CaseRunRow, mandatory_checks: list[CaseMandatoryCheckRow]) -> None:
    initialize()
    case_id = case.case_id
    with session_scope() as session:
        row = session.get(CaseRunRow, case_id)
        if row is None:
            session.add(case)
        else:
            _write_case_row(row, case)
        _replace_mandatory_checks(session=session, case_id=case_id, checks=mandatory_checks)


def get_case_state(case_id: CaseId) -> CaseRunRow:
    initialize()
    with session_scope() as session:
        row = session.get(CaseRunRow, str(case_id))
        if row is None:
            raise KeyError(f"case not found: {case_id}")
        return row


def save_case(case: CaseRunRow) -> None:
    initialize()
    case_id = case.case_id
    with session_scope() as session:
        lock_case_row(session, case_id)
        row = session.get(CaseRunRow, case_id)
        if row is None:
            raise KeyError(f"case not found: {case_id}")
        _write_case_row(row, case)


def set_case_status(case_id: CaseId, status: CaseStatus) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        row = session.get(CaseRunRow, case_str)
        if row is None:
            raise KeyError(f"case not found: {case_str}")
        row.status = status.value
        row.updated_at = now_utc()


def list_mandatory_checks(case_id: CaseId) -> list[CaseMandatoryCheckRow]:
    initialize()
    with session_scope() as session:
        return list(
            session.scalars(
                select(CaseMandatoryCheckRow)
                .where(CaseMandatoryCheckRow.case_id == str(case_id))
                .order_by(CaseMandatoryCheckRow.check_id)
            ).all()
        )


def replace_mandatory_checks(case_id: str, checks: list[CaseMandatoryCheckRow]) -> None:
    initialize()
    with session_scope() as session:
        lock_case_row(session, case_id)
        _replace_mandatory_checks(session=session, case_id=case_id, checks=checks)


def _write_case_row(row: CaseRunRow, case: CaseRunRow) -> None:
    row.case_class = case.case_class
    row.status = case.status
    row.objective = case.objective
    row.mode = case.mode
    row.playbook_policy = case.playbook_policy
    row.timeout_at = case.timeout_at
    row.completion_require_objective_satisfied = case.completion_require_objective_satisfied
    row.completion_require_evidence_completeness = case.completion_require_evidence_completeness
    row.completion_require_confidence_threshold = case.completion_require_confidence_threshold
    row.completion_allow_stop_on_timeout = case.completion_allow_stop_on_timeout
    row.request_source_channel = case.request_source_channel
    row.request_requester = case.request_requester
    row.request_tags = list(case.request_tags)
    row.escalation_required = case.escalation_required
    row.loop_count = case.loop_count
    row.last_novelty_signal = case.last_novelty_signal
    row.critic_depth_multiplier = case.critic_depth_multiplier
    row.updated_at = now_utc()


def _replace_mandatory_checks(
    session: Session,
    case_id: str,
    checks: list[CaseMandatoryCheckRow],
) -> None:
    session.execute(delete(CaseMandatoryCheckRow).where(CaseMandatoryCheckRow.case_id == case_id))
    for check in checks:
        check.case_id = case_id
        session.add(check)
