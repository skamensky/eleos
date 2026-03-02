from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

import httpx

ROOT = Path(__file__).resolve().parents[2]
BASE_COMPOSE = ROOT / "test_env" / "supabase" / "docker-compose.yml"
ELEOS_COMPOSE = ROOT / "test_env" / "supabase" / "docker-compose.eleos.yml"
API_BASE_URL = os.getenv("ELEOS_API_BASE_URL", "http://127.0.0.1:8080")
SUPPORT_MIGRATIONS = [
    ROOT / "test_env" / "supabase" / "supabase" / "migrations" / "0001_support_dataset.sql",
    ROOT / "test_env" / "supabase" / "supabase" / "migrations" / "0002_main_user_readonly.sql",
]
PLAYBOOK_SQL = ROOT / "test_env" / "supabase" / "playbooks" / "supabase_starter_playbooks.sql"

DEFAULT_OBJECTIVES = [
    "Investigate incident: permission denied and timeout errors in customer profile sync",
    "Investigate billing anomaly in support environment",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full Supabase-first Eleos end-to-end flow."
    )
    parser.add_argument(
        "--keep-up",
        action="store_true",
        help="Do not tear down docker compose stack",
    )
    parser.add_argument("--objective", action="append", help="Objective to run (repeatable)")
    parser.add_argument(
        "--mode",
        choices=["deep_investigation", "fast_mode"],
        default="fast_mode",
        help="Investigation mode for E2E runs",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=int,
        default=8,
        help="Per-case timeout minutes for E2E runs",
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY must be set")

    objectives = args.objective or DEFAULT_OBJECTIVES
    failures = 0
    try:
        _compose(["up", "-d", "--build"])
        _compose_exec_sql("CREATE SCHEMA IF NOT EXISTS experiment;", service="eleos-db")
        _compose(["exec", "-T", "eleos-api", "uv", "run", "alembic", "upgrade", "head"])
        _compose_exec_sql_files(SUPPORT_MIGRATIONS, service="supabase-db")
        _compose_exec_sql_files([PLAYBOOK_SQL], service="eleos-db")
        _wait_for_api()

        for objective in objectives:
            payload = _run_objective(
                objective,
                mode=args.mode,
                timeout_minutes=args.timeout_minutes,
            )
            print(json.dumps(payload, indent=2))
            evidence_ref_count = cast(int, payload.get("evidence_ref_count", 0))
            if evidence_ref_count <= 0:
                failures += 1
                print(
                    f"Objective produced zero evidence refs: {objective}",
                    file=sys.stderr,
                )
    finally:
        if not args.keep_up:
            _compose(["down", "-v"], check=False)

    if failures:
        raise SystemExit(1)


def _run_objective(objective: str, *, mode: str, timeout_minutes: int) -> dict[str, object]:
    with httpx.Client(timeout=_api_request_timeout(timeout_minutes)) as client:
        response = client.post(
            f"{API_BASE_URL}/v1/investigations",
            json={
                "objective": objective,
                "mode": mode,
                "timeout_minutes": timeout_minutes,
            },
        )
    if response.status_code != 200:
        raise RuntimeError(
            f"investigation run failed ({response.status_code}): {response.text}"
        )
    data = response.json()
    report = _as_dict(data.get("report"))
    evidence_ledger_refs = [str(item) for item in _as_list(report.get("evidence_ledger_refs"))]
    citations = [str(item) for item in _as_list(report.get("citations"))]
    return {
        "case_id": str(data.get("case_id", "")),
        "objective": str(report.get("objective", "")),
        "final_assessment": str(report.get("final_assessment", "")),
        "confidence_score": _as_float(report.get("confidence_score")),
        "confidence_label": str(report.get("confidence_label", "")),
        "completion_gate_passed": bool(
            _as_dict(report.get("completion_gate_status")).get("passed", False)
        ),
        "evidence_ref_count": int(len(evidence_ledger_refs)),
        "evidence_ledger_refs": evidence_ledger_refs,
        "citation_count": int(len(citations)),
        "escalation": report.get("escalation"),
    }


def _wait_for_api(timeout_seconds: int = 90) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None
    with httpx.Client(timeout=3) as client:
        while time.monotonic() < deadline:
            try:
                response = client.get(f"{API_BASE_URL}/health")
                if response.status_code == 200:
                    return
                last_error = f"status={response.status_code}"
            except httpx.HTTPError as exc:
                last_error = str(exc)
            time.sleep(1)
    raise RuntimeError(f"API did not become healthy: {last_error}")


def _as_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return list(value)
    return []


def _as_float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _api_request_timeout(timeout_minutes: int) -> float:
    return float(max(600, (timeout_minutes + 5) * 60))


def _compose_exec_sql_files(paths: list[Path], *, service: str) -> None:
    for path in paths:
        _compose_exec_sql(path.read_text(encoding="utf-8"), service=service)


def _compose_exec_sql(sql_text: str, *, service: str) -> None:
    _compose(
        [
            "exec",
            "-T",
            service,
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "postgres",
            "-d",
            "postgres",
        ],
        input_text=sql_text,
    )


def _compose(
    args: list[str],
    *,
    check: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "docker",
        "compose",
        "-f",
        str(BASE_COMPOSE),
        "-f",
        str(ELEOS_COMPOSE),
        *args,
    ]
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
        input=input_text,
        cwd=ROOT,
    )


if __name__ == "__main__":
    main()
