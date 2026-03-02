from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from eleos.core.tool_inputs import build_tool_input_payload
from eleos.core.tools import McpToolRegistry, get_mcp_tool_registry
from eleos.db.models import TaskRow, ToolExecutionRow
from eleos.models.enums import ToolExecutionStatus
from eleos.models.tool_execution import ToolRunResult

_tool_registry: McpToolRegistry = get_mcp_tool_registry()


def start_tool_execution(task: TaskRow) -> ToolExecutionRow:
    started_at = datetime.now(timezone.utc)
    input_handle = f"input://{task.task_id}/{uuid4()}"
    return ToolExecutionRow(
        tool_execution_id=str(uuid4()),
        case_id=task.case_id,
        tool_name=task.tool_name,
        status=ToolExecutionStatus.RUNNING.value,
        started_at=started_at,
        finished_at=None,
        duration_ms=None,
        input_handle=input_handle,
        error=None,
    )


def run_tool_plan(task: TaskRow) -> ToolRunResult:
    return _tool_registry.run(task.tool_name, build_tool_input_payload(task))


def finish_tool_execution(
    execution: ToolExecutionRow,
    result: ToolRunResult,
) -> ToolExecutionRow:
    finished_at = datetime.now(timezone.utc)
    duration_ms = int((finished_at - execution.started_at).total_seconds() * 1000)
    status = ToolExecutionStatus.FAILED if result.failed else ToolExecutionStatus.SUCCEEDED
    execution.status = status.value
    execution.finished_at = finished_at
    execution.duration_ms = duration_ms
    execution.error = result.error
    return execution
