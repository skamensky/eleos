from __future__ import annotations

from sqlalchemy import delete, func, or_, select

from eleos.db.engine import session_scope
from eleos.db.models import (
    EvidenceRecordRow,
    HypothesisRow,
    TaskEvidenceLinkRow,
    TaskHypothesisLinkRow,
    TaskRow,
)
from eleos.db.state_support import initialize, lock_case_row, now_utc
from eleos.models.enums import TaskStatus
from eleos.models.ids import CaseId, HypothesisId, as_hypothesis_id


def save_tasks(case_id: CaseId, tasks: list[TaskRow]) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        existing = {
            row.task_id: row
            for row in session.scalars(select(TaskRow).where(TaskRow.case_id == case_str)).all()
        }
        for task in tasks:
            task.case_id = case_str
            row = existing.pop(task.task_id, None)
            if row is None:
                session.add(task)
            else:
                _write_task_row(row, task)

        for stale in existing.values():
            session.delete(stale)


def list_tasks(case_id: CaseId) -> list[TaskRow]:
    initialize()
    with session_scope() as session:
        return list(
            session.scalars(
                select(TaskRow)
                .where(TaskRow.case_id == str(case_id))
                .order_by(TaskRow.priority.asc(), TaskRow.updated_at.asc())
            ).all()
        )


def list_pending_tasks(case_id: CaseId) -> list[TaskRow]:
    initialize()
    with session_scope() as session:
        return list(
            session.scalars(
                select(TaskRow)
                .where(TaskRow.case_id == str(case_id))
                .where(TaskRow.status == TaskStatus.PENDING.value)
                .order_by(TaskRow.priority.asc(), TaskRow.updated_at.asc())
            ).all()
        )


def has_pending_tasks(case_id: CaseId) -> bool:
    initialize()
    with session_scope() as session:
        pending_id = session.scalar(
            select(TaskRow.task_id)
            .where(TaskRow.case_id == str(case_id))
            .where(TaskRow.status == TaskStatus.PENDING.value)
            .limit(1)
        )
        return pending_id is not None


def has_pending_task_with_expected_value_at_least(
    case_id: CaseId,
    expected_value_floor: float,
) -> bool:
    initialize()
    with session_scope() as session:
        pending_id = session.scalar(
            select(TaskRow.task_id)
            .where(TaskRow.case_id == str(case_id))
            .where(TaskRow.status == TaskStatus.PENDING.value)
            .where(TaskRow.expected_value >= expected_value_floor)
            .limit(1)
        )
        return pending_id is not None


def max_task_priority(case_id: CaseId) -> int:
    initialize()
    with session_scope() as session:
        max_priority = session.scalar(
            select(func.max(TaskRow.priority)).where(TaskRow.case_id == str(case_id))
        )
        return int(max_priority or 0)


def list_forced_pending_tasks(case_id: CaseId, required_step_ids: set[str]) -> list[TaskRow]:
    if not required_step_ids:
        return []
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        required_step_tools_subquery = (
            select(TaskRow.tool_name)
            .where(TaskRow.case_id == case_str)
            .where(TaskRow.created_reason.in_(required_step_ids))
        )
        return list(
            session.scalars(
                select(TaskRow)
                .where(TaskRow.case_id == case_str)
                .where(TaskRow.status == TaskStatus.PENDING.value)
                .where(
                    or_(
                        TaskRow.created_reason.in_(required_step_ids),
                        TaskRow.tool_name.in_(required_step_tools_subquery),
                    )
                )
                .order_by(TaskRow.priority.asc(), TaskRow.updated_at.asc())
            ).all()
        )


def set_task_hypothesis_links(
    case_id: CaseId,
    task_id: str,
    hypothesis_ids: list[HypothesisId],
) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        task = session.get(TaskRow, task_id)
        if task is None or task.case_id != case_str:
            raise KeyError(f"task not found: {task_id}")

        session.execute(
            delete(TaskHypothesisLinkRow).where(TaskHypothesisLinkRow.task_id == task_id)
        )

        for hypothesis_id in dict.fromkeys(hypothesis_ids):
            hypothesis = session.get(HypothesisRow, hypothesis_id)
            if hypothesis is None or hypothesis.case_id != case_str:
                raise KeyError(f"hypothesis not found: {hypothesis_id}")
            session.add(
                TaskHypothesisLinkRow(
                    task_id=task_id,
                    hypothesis_id=hypothesis_id,
                )
            )


def copy_task_hypothesis_links(
    case_id: CaseId,
    source_task_id: str,
    target_task_id: str,
) -> None:
    source_hypothesis_ids = list_task_hypothesis_ids(source_task_id)
    set_task_hypothesis_links(case_id, target_task_id, source_hypothesis_ids)


def list_task_hypothesis_ids(task_id: str) -> list[HypothesisId]:
    initialize()
    with session_scope() as session:
        return [
            as_hypothesis_id(row.hypothesis_id)
            for row in session.scalars(
                select(TaskHypothesisLinkRow)
                .where(TaskHypothesisLinkRow.task_id == task_id)
                .order_by(TaskHypothesisLinkRow.hypothesis_id.asc())
            ).all()
        ]


def add_task_evidence_ref(
    case_id: CaseId,
    task_id: str,
    evidence_id: str,
) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)

        task = session.get(TaskRow, task_id)
        if task is None or task.case_id != case_str:
            raise KeyError(f"task not found: {task_id}")

        evidence = session.get(EvidenceRecordRow, evidence_id)
        if evidence is None or evidence.case_id != case_str:
            raise KeyError(f"evidence not found: {evidence_id}")

        row = session.get(TaskEvidenceLinkRow, (task_id, evidence_id))
        if row is None:
            session.add(TaskEvidenceLinkRow(task_id=task_id, evidence_id=evidence_id))


def list_task_evidence_ids(task_id: str) -> list[str]:
    initialize()
    with session_scope() as session:
        return [
            row.evidence_id
            for row in session.scalars(
                select(TaskEvidenceLinkRow)
                .where(TaskEvidenceLinkRow.task_id == task_id)
                .order_by(TaskEvidenceLinkRow.evidence_id.asc())
            ).all()
        ]


def _write_task_row(row: TaskRow, task: TaskRow) -> None:
    row.case_id = task.case_id
    row.linked_hypothesis_id = task.linked_hypothesis_id
    row.intent = task.intent
    row.expected_evidence = task.expected_evidence
    row.expected_information_gain = task.expected_information_gain
    row.expected_value = task.expected_value
    row.tool_name = task.tool_name
    row.tool_input_objective = task.tool_input_objective
    row.tool_input_step = task.tool_input_step
    row.tool_input_reason = task.tool_input_reason
    row.tool_input_evidence_id = task.tool_input_evidence_id
    row.status = task.status
    row.priority = task.priority
    row.created_reason = task.created_reason
    row.updated_at = now_utc()
