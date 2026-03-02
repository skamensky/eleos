from __future__ import annotations

from eleos.core.tool_catalog import get_tool_catalog
from eleos.db.models import TaskRow
from eleos.models.payloads import ToolInputPayload


def build_tool_input_payload(task: TaskRow) -> ToolInputPayload:
    context = _task_context(task)
    catalog = get_tool_catalog()
    entry = catalog.get(task.tool_name)
    if entry is None:
        return _strip_none_values(context)
    if not entry.input_field_map:
        return _strip_none_values(context)
    payload: ToolInputPayload = {}
    for field_name, context_key in entry.input_field_map.items():
        if context_key not in context:
            continue
        value = context[context_key]
        if value is None:
            continue
        payload[field_name] = value
    return payload


def _task_context(task: TaskRow) -> dict[str, object | None]:
    return {
        "objective": task.tool_input_objective,
        "step": task.tool_input_step,
        "reason": task.tool_input_reason,
        "evidence_id": task.tool_input_evidence_id,
        "task_id": task.task_id,
        "intent": task.intent,
        "expected_evidence": task.expected_evidence,
        "case_id": task.case_id,
    }


def _strip_none_values(value: dict[str, object | None]) -> ToolInputPayload:
    payload: ToolInputPayload = {}
    for key, raw in value.items():
        if raw is not None:
            payload[key] = raw
    return payload
