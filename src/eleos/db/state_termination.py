from __future__ import annotations

from sqlalchemy import select

from eleos.db.engine import session_scope
from eleos.db.models import TerminationSnapshotRow
from eleos.db.state_support import initialize, lock_case_row
from eleos.models.ids import CaseId


def save_termination_snapshot(
    case_id: CaseId,
    loop_count: int,
    snapshot: TerminationSnapshotRow,
) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        row = session.get(TerminationSnapshotRow, (case_str, loop_count))
        if row is None:
            snapshot.case_id = case_str
            snapshot.loop_count = loop_count
            session.add(snapshot)
            return
        _write_termination_row(row, snapshot)


def latest_termination_snapshot(case_id: CaseId) -> TerminationSnapshotRow | None:
    initialize()
    with session_scope() as session:
        return session.scalars(
            select(TerminationSnapshotRow)
            .where(TerminationSnapshotRow.case_id == str(case_id))
            .order_by(TerminationSnapshotRow.loop_count.desc())
            .limit(1)
        ).first()


def _write_termination_row(row: TerminationSnapshotRow, snapshot: TerminationSnapshotRow) -> None:
    row.objective_satisfied = snapshot.objective_satisfied
    row.evidence_completeness_sufficient = snapshot.evidence_completeness_sufficient
    row.confidence_sufficient = snapshot.confidence_sufficient
    row.timeout_reached = snapshot.timeout_reached
    row.no_novel_signal = snapshot.no_novel_signal
    row.expected_value_below_threshold = snapshot.expected_value_below_threshold
    row.escalation_required = snapshot.escalation_required
    row.should_stop = snapshot.should_stop
    row.reason = snapshot.reason
