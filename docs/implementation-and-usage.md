# Implementation And Usage

This document contains implementation-level and operational details that are intentionally kept out of the top-level README.

## Run (CLI)

```bash
uv run eleos investigate "Investigate outage in payments-api with permission denied errors"
```

Options:
- `--mode deep_investigation|fast_mode`
- `--policy suggestive|mandatory`
- `--timeout-minutes <int>`

## REST API

Run the HTTP service:

```bash
uv run uvicorn eleos.api.app:app --host 0.0.0.0 --port 8080
```

Start an investigation:

```bash
curl -sS http://127.0.0.1:8080/v1/investigations \
  -H "content-type: application/json" \
  -d '{
    "objective": "Investigate outage in payments-api with permission denied errors",
    "mode": "fast_mode",
    "playbook_policy": "suggestive",
    "timeout_minutes": 8
  }'
```

## Persistence

Runtime state is DB-first and persisted in Postgres via SQLAlchemy + Alembic.

Required config:
- `ELEOS_PERSISTENCE__DSN=postgresql://...`
- `ELEOS_PERSISTENCE__DB_SCHEMA=experiment`

Apply migrations:

```bash
uv run alembic upgrade head
```

Primary tables (under `experiment` by default):
- `case_runs`
- `case_mandatory_checks`
- `case_hypotheses`
- `case_tasks`
- `tool_executions`
- `tool_outputs`
- `evidence_records`
- `cognition_records`
- `termination_snapshots`
- `case_final_reports`
- `case_final_report_checks`
- `playbooks`
- `playbook_steps`

Playbooks are DB-backed only. There are no in-code default playbooks.

## LLM Configuration

- `ELEOS_LLM__MODEL=openai:gpt-5.2`
- `ELEOS_LLM__BASE_URL=https://api.openai.com/v1`

`ELEOS_LLM__BASE_URL` can point to an OpenAI-compatible gateway (for example LiteLLM).

## MCP Tool Configuration

Tools are MCP-only and configured explicitly per deployment/environment.
There are no built-in local tools in runtime.

Use a JSON array for `ELEOS_TOOLS__MCP_SERVERS`:

```bash
export ELEOS_TOOLS__MCP_SERVERS='[
  {
    "server_id": "observability",
    "enabled": true,
    "transport": {
      "type": "streamable_http",
      "url": "https://mcp.example.com/observability",
      "headers": {"x-tenant-id": "acme"},
      "auth": {"type": "bearer_token", "token_env_var": "OBS_MCP_TOKEN"},
      "connect_timeout_seconds": 5,
      "read_timeout_seconds": 30,
      "verify_tls": true
    },
    "declared_tools": ["log_scan", "trace_lookup"],
    "tool_name_prefix": "obs/",
    "initialize_timeout_seconds": 10,
    "request_timeout_seconds": 30,
    "max_retries": 2,
    "retry_backoff_seconds": 0.2
  },
  {
    "server_id": "identity",
    "enabled": true,
    "transport": {
      "type": "stdio",
      "command": "uvx",
      "args": ["acme-identity-mcp-server"],
      "env": {"ENVIRONMENT": "prod"}
    },
    "include_tools": ["iam_audit", "binding_diff"],
    "allow_unscoped_tool_names": true
  }
]'
```

Routing conventions:
- Explicit namespaced tool: `server_id/tool_name` (for example `observability/log_scan`)
- Declared prefix route: `tool_name_prefix + tool_name` (for example `obs/log_scan`)
- Optional unscoped tool names when exactly one server opts in with `allow_unscoped_tool_names=true`

## Supabase-First Test Environment

Supabase-first E2E assets live under `test_env/supabase/`.

- Base stack: `test_env/supabase/docker-compose.yml`
- Eleos overlay: `test_env/supabase/docker-compose.eleos.yml`
- Separate databases:
  - `supabase-db` for Supabase fixture/metadata/tool data
  - `eleos-db` for Eleos runtime state (`experiment` schema)
- `eleos-api` serves both API + static UI at `http://127.0.0.1:8080`
- Tool catalog: `test_env/supabase/config/tools_catalog.toml`
- Starter playbooks: `test_env/supabase/playbooks/supabase_starter_playbooks.sql`
- Single full-run script: `scripts/e2e/run_supabase_e2e.py`

Quick commands:

```bash
make supabase-up
make supabase-e2e
make supabase-down
```

## Frontend Type Sync (OpenAPI)

Frontend API types are generated from backend OpenAPI, not maintained manually.

```bash
make openapi      # writes docs/eleos-openapi.json
make web-types    # writes web/src/lib/api/generated.ts
```

`web` also regenerates types automatically on `npm run dev` and `npm run build`.
