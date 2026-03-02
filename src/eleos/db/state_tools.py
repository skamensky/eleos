from __future__ import annotations

from eleos.db.engine import session_scope
from eleos.db.models import ToolExecutionRow
from eleos.db.state_support import initialize, lock_case_row, now_utc
from eleos.models.ids import CaseId


def save_tool_execution(case_id: CaseId, execution: ToolExecutionRow) -> None:
    initialize()
    case_str = str(case_id)
    with session_scope() as session:
        lock_case_row(session, case_str)
        row = session.get(ToolExecutionRow, execution.tool_execution_id)
        if row is None:
            execution.case_id = case_str
            session.add(execution)
            return
        _write_tool_execution_row(row, case_str, execution)


def get_tool_execution(tool_execution_id: str) -> ToolExecutionRow:
    initialize()
    with session_scope() as session:
        row = session.get(ToolExecutionRow, tool_execution_id)
        if row is None:
            raise KeyError(f"tool execution not found: {tool_execution_id}")
        return row


def _write_tool_execution_row(
    row: ToolExecutionRow,
    case_id: str,
    execution: ToolExecutionRow,
) -> None:
    row.case_id = case_id
    row.tool_name = execution.tool_name
    row.status = execution.status
    row.started_at = execution.started_at
    row.finished_at = execution.finished_at
    row.duration_ms = execution.duration_ms
    row.input_handle = execution.input_handle
    row.error = execution.error
    row.updated_at = now_utc()
