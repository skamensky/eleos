from __future__ import annotations

import os
import re
from typing import Any, cast

import httpx
import psycopg
from fastapi import FastAPI
from psycopg import sql as pg_sql
from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    tool_name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    tool_definition: dict[str, Any] = Field(default_factory=dict)


class InvokeResponse(BaseModel):
    source: str
    summary: str
    raw_payload: dict[str, Any]
    anomalies: list[str] = Field(default_factory=list)
    confidence_impact: float = 0.0
    novelty_signal: float = 0.0
    failed: bool = False
    error: str | None = None


app = FastAPI(title="MCP Supabase Example")
DB_DSN = os.getenv("MCP_DB_DSN", "postgresql://app_user:app_user@db:5432/postgres")
META_BASE_URL = os.getenv("MCP_META_BASE_URL", "http://meta:8080")
READONLY_SQL_FORBIDDEN_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|comment|copy)\b",
    re.IGNORECASE,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/invoke")
def invoke(request: InvokeRequest) -> InvokeResponse:
    tool = request.tool_name
    if tool == "log_scan":
        return _log_scan(request)
    if tool == "function_runs":
        return _function_runs(request)
    if tool == "auth_timeline":
        return _auth_timeline(request)
    if tool == "access_path_explain":
        return _access_path_explain(request)
    if tool == "metadata_api_inspect":
        return _metadata_api_inspect(request)
    if tool == "sql_readonly":
        return _sql_readonly(request)
    return _error_response(tool, f"unknown tool: {tool}")


def _log_scan(request: InvokeRequest) -> InvokeResponse:
    rows = _query(
        """
        SELECT level, message, request_id, user_id, created_at
        FROM public.support_app_logs
        ORDER BY created_at DESC
        LIMIT 200
        """
    )
    errors = [row for row in rows if str(row.get("level", "")).upper() == "ERROR"]
    summary = f"Scanned {len(rows)} support logs. Errors: {len(errors)}"
    anomalies: list[str] = []
    if errors:
        anomalies.append("error_cluster")
    return InvokeResponse(
        source="mcp:supabase/log_scan",
        summary=summary,
        raw_payload={
            "rows": rows,
            "tool_definition": request.tool_definition,
        },
        anomalies=anomalies,
        confidence_impact=0.2 if errors else 0.05,
        novelty_signal=0.6 if errors else 0.2,
    )


def _function_runs(request: InvokeRequest) -> InvokeResponse:
    rows = _query(
        """
        SELECT function_name, status, latency_ms, error_class, version, started_at
        FROM public.support_function_runs
        ORDER BY started_at DESC
        LIMIT 200
        """
    )
    failed = [row for row in rows if str(row.get("status", "")).lower() != "succeeded"]
    summary = f"Reviewed {len(rows)} function runs. Failures: {len(failed)}"
    anomalies: list[str] = []
    if failed:
        anomalies.append("function_failure_cluster")
    return InvokeResponse(
        source="mcp:supabase/function_runs",
        summary=summary,
        raw_payload={
            "rows": rows,
            "tool_definition": request.tool_definition,
        },
        anomalies=anomalies,
        confidence_impact=0.25 if failed else 0.05,
        novelty_signal=0.65 if failed else 0.25,
    )


def _auth_timeline(request: InvokeRequest) -> InvokeResponse:
    rows = _query(
        """
        SELECT user_id, event_type, provider, status, detail, occurred_at
        FROM public.support_auth_events
        ORDER BY occurred_at DESC
        LIMIT 200
        """
    )
    failures = [row for row in rows if str(row.get("status", "")).lower() == "failed"]
    summary = f"Built auth timeline from {len(rows)} events. Failures: {len(failures)}"
    anomalies: list[str] = []
    if failures:
        anomalies.append("auth_failure_signal")
    return InvokeResponse(
        source="mcp:supabase/auth_timeline",
        summary=summary,
        raw_payload={
            "rows": rows,
            "tool_definition": request.tool_definition,
        },
        anomalies=anomalies,
        confidence_impact=0.2 if failures else 0.05,
        novelty_signal=0.55 if failures else 0.2,
    )


def _access_path_explain(request: InvokeRequest) -> InvokeResponse:
    rows = _query(
        """
        SELECT actor_id, resource, action, allowed, denial_reason, occurred_at
        FROM public.support_access_events
        ORDER BY occurred_at DESC
        LIMIT 200
        """
    )
    denied = [row for row in rows if row.get("allowed") is False]
    summary = f"Analyzed {len(rows)} access events. Denied paths: {len(denied)}"
    anomalies: list[str] = []
    if denied:
        anomalies.append("access_deny_cluster")
    return InvokeResponse(
        source="mcp:supabase/access_path_explain",
        summary=summary,
        raw_payload={
            "rows": rows,
            "tool_definition": request.tool_definition,
        },
        anomalies=anomalies,
        confidence_impact=0.2 if denied else 0.05,
        novelty_signal=0.5 if denied else 0.2,
    )


def _metadata_api_inspect(request: InvokeRequest) -> InvokeResponse:
    resource = str(request.payload.get("resource", "tables"))
    allowed = {"schemas", "tables", "columns", "extensions"}
    if resource not in allowed:
        return _error_response(
            "metadata_api_inspect",
            f"resource '{resource}' not allowed; choose one of {sorted(allowed)}",
        )
    schema = str(request.payload.get("schema", "public"))
    path = _resource_path(resource, schema)
    url = f"{META_BASE_URL}{path}"
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001
        return _error_response("metadata_api_inspect", f"metadata api failure: {exc}")
    summary = f"Fetched metadata resource '{resource}' from Supabase metadata API."
    return InvokeResponse(
        source="mcp:supabase/metadata_api_inspect",
        summary=summary,
        raw_payload={
            "resource": resource,
            "schema": schema,
            "metadata": data,
            "tool_definition": request.tool_definition,
        },
        confidence_impact=0.1,
        novelty_signal=0.4,
    )


def _sql_readonly(request: InvokeRequest) -> InvokeResponse:
    objective = str(request.payload.get("objective", "")).lower()
    sql = str(request.payload.get("sql", "")).strip()
    if not sql:
        sql = _default_sql_for_objective(objective)
    sql = sql.strip()
    if not sql.lower().startswith("select"):
        return _error_response("sql_readonly", "only SELECT statements are allowed")
    if ";" in sql:
        return _error_response("sql_readonly", "multi-statement SQL is not allowed")
    if READONLY_SQL_FORBIDDEN_PATTERN.search(sql):
        return _error_response("sql_readonly", "forbidden SQL keyword for readonly mode")

    rows = _query(sql, row_limit=500)
    summary = f"Executed read-only SQL; returned {len(rows)} row(s)."
    return InvokeResponse(
        source="mcp:supabase/sql_readonly",
        summary=summary,
        raw_payload={
            "sql": sql,
            "rows": rows,
            "tool_definition": request.tool_definition,
        },
        confidence_impact=0.15,
        novelty_signal=0.45,
    )


def _query(sql: str, row_limit: int | None = None) -> list[dict[str, Any]]:
    statement = sql
    if row_limit is not None and " limit " not in sql.lower():
        statement = f"{sql.rstrip()} LIMIT {row_limit}"
    with psycopg.connect(DB_DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(pg_sql.SQL(statement))
            if cur.description is None:
                return []
            columns = [desc.name for desc in cur.description]
            rows = cur.fetchall()
    safe_rows = cast(list[tuple[object, ...]], rows)
    return [{columns[index]: value for index, value in enumerate(row)} for row in safe_rows]


def _resource_path(resource: str, schema: str) -> str:
    if resource == "schemas":
        return "/schemas"
    if resource == "tables":
        return f"/tables?included_schemas={schema}"
    if resource == "columns":
        return f"/columns?included_schemas={schema}"
    if resource == "extensions":
        return "/extensions"
    raise ValueError(f"unsupported metadata resource: {resource}")


def _default_sql_for_objective(objective: str) -> str:
    if "bill" in objective or "cost" in objective or "spend" in objective:
        return """
        SELECT function_name, count(*) AS failure_count
        FROM public.support_function_runs
        WHERE status != 'succeeded'
        GROUP BY function_name
        ORDER BY failure_count DESC
        """
    return """
    SELECT level, count(*) AS entry_count
    FROM public.support_app_logs
    GROUP BY level
    ORDER BY entry_count DESC
    """


def _error_response(tool_name: str, error: str) -> InvokeResponse:
    return InvokeResponse(
        source=f"mcp:supabase/{tool_name}",
        summary=f"Tool failed: {tool_name}",
        raw_payload={"error": error},
        failed=True,
        error=error,
    )
