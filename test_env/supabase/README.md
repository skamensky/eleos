# Supabase-First E2E Environment

This directory contains a Supabase-first test environment for Eleos.

## Compose files

- `docker-compose.yml`: base Supabase services (`supabase-db`, `meta`, `rest`, `auth`, `studio`)
- `docker-compose.eleos.yml`: adds `eleos-db`, `eleos-api` (serves API + static UI), and `mcp-supabase-example`

Run with both:

```bash
docker compose \
  -f test_env/supabase/docker-compose.yml \
  -f test_env/supabase/docker-compose.eleos.yml \
  up -d --build
```

## Key assets

- `supabase/config.toml`: local Supabase config
- `config/tools_catalog.toml`: config-driven tool catalog with function descriptions/source definitions
- `playbooks/supabase_starter_playbooks.sql`: Supabase-only starter playbooks
- `mcp_supabase_example/`: example MCP server exposing `supabase/*` tools

## Single E2E runner

Use one script for the full run:

```bash
uv run python scripts/e2e/run_supabase_e2e.py
```

The script calls the HTTP API (`/v1/investigations`) on `eleos-api` instead of using inline Python execution.

Database separation:
- Supabase services + MCP fixture queries use `supabase-db`.
- Eleos runtime persistence (`experiment` schema) uses `eleos-db`.

Local ports:
- `http://127.0.0.1:8080` -> `eleos-api` (REST API + UI)
