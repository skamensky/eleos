from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from eleos.api.data import (
    create_playbook,
    get_case_run_detail,
    get_case_run_timeline,
    get_playbook_form_options,
    list_case_runs,
    list_playbooks,
)
from eleos.api.models import (
    CaseRunDetailResponse,
    CaseRunSummaryResponse,
    CaseRunTimelineResponse,
    InvestigationRunResponse,
    PlaybookCreateRequest,
    PlaybookFormOptionsResponse,
    to_final_report_response,
)
from eleos.core.runtime import InvestigationRuntime
from eleos.db.views.models import PlaybookView
from eleos.models.case import InvestigationRequest

app = FastAPI(title="Eleos API", version="0.1.0")
_runtime: InvestigationRuntime | None = None
_api_prefixes = ("v1/", "health", "docs", "openapi.json", "redoc")


def _cors_origins() -> list[str]:
    raw = os.getenv("ELEOS_API_CORS_ORIGINS", "")
    if not raw:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    if "*" in origins:
        return ["*"]
    return origins


def _cors_allow_credentials(origins: list[str]) -> bool:
    return origins != ["*"]


def _ui_dist_dir() -> Path:
    configured = os.getenv("ELEOS_UI_DIST_PATH", "/workspace/web-dist")
    return Path(configured)


def _ui_index_path() -> Path:
    return _ui_dist_dir() / "index.html"


def _ui_is_available() -> bool:
    return _ui_index_path().is_file()


_resolved_cors_origins = _cors_origins()


app.add_middleware(
    cast(Any, CORSMiddleware),
    allow_origins=_resolved_cors_origins,
    allow_credentials=_cors_allow_credentials(_resolved_cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str


def get_runtime() -> InvestigationRuntime:
    global _runtime
    if _runtime is None:
        _runtime = InvestigationRuntime()
    return _runtime


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/v1/investigations", response_model=InvestigationRunResponse)
async def run_investigation(request: InvestigationRequest) -> InvestigationRunResponse:
    case_id, report = await run_in_threadpool(get_runtime().run_with_case_id, request)
    return InvestigationRunResponse(
        case_id=case_id,
        report=to_final_report_response(report),
    )


@app.get("/v1/playbooks", response_model=list[PlaybookView])
async def get_playbooks(limit: int = Query(100, ge=1, le=500)) -> list[PlaybookView]:
    return await run_in_threadpool(list_playbooks, limit=limit)


@app.get("/v1/playbook-form-options", response_model=PlaybookFormOptionsResponse)
async def get_playbook_options() -> PlaybookFormOptionsResponse:
    return await run_in_threadpool(get_playbook_form_options)


@app.post("/v1/playbooks", response_model=PlaybookView)
async def post_playbook(payload: PlaybookCreateRequest) -> PlaybookView:
    try:
        created = await run_in_threadpool(create_playbook, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return created


@app.get("/v1/case-runs", response_model=list[CaseRunSummaryResponse])
async def get_case_runs(limit: int = Query(100, ge=1, le=500)) -> list[CaseRunSummaryResponse]:
    return await run_in_threadpool(list_case_runs, limit=limit)


@app.get("/v1/case-runs/{case_id}", response_model=CaseRunDetailResponse)
async def get_case_run(case_id: str) -> CaseRunDetailResponse:
    row = await run_in_threadpool(get_case_run_detail, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"case run not found: {case_id}")
    return row


@app.get("/v1/case-runs/{case_id}/timeline", response_model=CaseRunTimelineResponse)
async def get_case_run_timeline_route(case_id: str) -> CaseRunTimelineResponse:
    timeline = await run_in_threadpool(get_case_run_timeline, case_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail=f"case run not found: {case_id}")
    return timeline


@app.get("/", include_in_schema=False)
def ui_root() -> FileResponse:
    index_path = _ui_index_path()
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="web ui not bundled")
    return FileResponse(index_path)


@app.get("/{ui_path:path}", include_in_schema=False)
def ui_asset_or_spa(ui_path: str) -> FileResponse:
    if any(ui_path == prefix or ui_path.startswith(prefix) for prefix in _api_prefixes):
        raise HTTPException(status_code=404, detail="not found")

    dist_dir = _ui_dist_dir()
    candidate = (dist_dir / ui_path).resolve()
    dist_root = dist_dir.resolve()
    if dist_root not in candidate.parents and candidate != dist_root:
        raise HTTPException(status_code=404, detail="not found")

    if candidate.is_file():
        return FileResponse(candidate)

    index_path = _ui_index_path()
    if _ui_is_available():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="web ui not bundled")
