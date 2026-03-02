# Supabase-First Testing Architecture for Eleos

## Scope
This document defines a clean testing architecture where Supabase is the first concrete environment.
It is focused on realistic support investigations without requiring full cloud infra deployment.

## Architecture (Supabase First Example)

1. Eleos Runtime
- Runs normal investigation graph and agent workflow.
- Uses production-like configuration (real LLM API key, real DB persistence).

2. Postgres State Store (Eleos)
- Eleos persists runtime state in its own Postgres schema (`experiment`).
- Playbooks are user-managed and preloaded explicitly.

3. Supabase Test Workspace
- Dedicated project/workspace with controlled test datasets.
- Holds support-relevant artifacts:
  - auth event history
  - function execution logs
  - application logs
  - policy snapshots / access metadata
  - schema metadata and migration history

4. MCP Layer (Supabase Tools)
- Eleos calls MCP tools only.
- MCP tools query Supabase datasets and return structured results.

5. E2E Evaluation Harness
- Runs case objectives against Eleos.
- Captures final report, evidence references, citations, completion checks.
- Compares output to expected investigation outcomes for each test case.

## Preview: Source Code Organization (No Implementation Yet)

Proposed layout for the Supabase-first testing layer:

```text
src/eleos/
  settings/
    tools.py
      # MCP server config, declared tool names, auth config
  core/
    tools.py
      # MCP dispatch + transport invocation
  models/
    tool_execution.py
      # Generic tool result contract only
      # No concrete per-tool input contracts in runtime code

test_env/
  supabase/
    README.md
      # How to run Supabase-first E2E tests
    docker-compose.yml
      # Supabase-native stack (db, auth, storage, rest, studio, etc.)
    docker-compose.eleos.yml
      # Adds Eleos runtime + MCP service to the Supabase stack
    supabase/
      config.toml
        # Supabase config file used by local stack
      migrations/
        # Optional test schema/data migrations
    config/
      tools_catalog.toml
        # Tool definitions + input schema references (config-driven)
      playbooks.toml
        # Playbook metadata/index for test setup
    fixtures/
      incidents/
      billing/
      auth/
      access/
      performance/
      metadata/
        # Replay datasets mapped to expected outcomes
    playbooks/
      supabase_starter_playbooks.sql
        # Supabase-only playbooks (incident, billing, general)
    mcp_supabase_example/
      README.md
      Dockerfile
      app.py
        # Example MCP server exposing supabase/* tools
      requirements.txt

scripts/
  e2e/
    run_supabase_e2e.py
      # Single script for full Supabase end-to-end run

docs/
  supabase-eleos-test-recommendations.md
    # This architecture + tool/playbook guidance
  supabase-test-cases.md
    # Concrete case catalog with expected outcomes
```

Module boundaries:
- `src/eleos/*` remains runtime/orchestrator logic only.
- `test_env/supabase/*` contains test-only assets and example MCP integration code.
- `scripts/e2e/*` contains one full-run E2E entrypoint only.
- No auto-seeding in runtime; playbook loading remains explicit/manual for tests.
- Tool input shape is config-driven (from tool catalog / MCP schemas), not hardcoded in runtime models.

## Starter Supabase MCP Tools

All tools below are Supabase-specific and read-only:

1. `supabase/log_scan`
- Query app/platform log datasets by window, severity, request id, user id.

2. `supabase/function_runs`
- Return function run outcomes, latency buckets, error clusters, deploy/version correlation.

3. `supabase/auth_timeline`
- Build a timeline of sign-in, refresh, revoke, MFA, provider errors for a user/session.

4. `supabase/access_path_explain`
- Explain access path failures (RLS/policy/role/claim) for a table/action/user context.

5. `supabase/metadata_api_inspect`
- Limited wrapper over Supabase metadata APIs (schemas/tables/columns/indexes/extensions).
- Expose only allowlisted metadata endpoints/queries needed for support diagnostics.

6. `supabase/sql_readonly`
- Arbitrary SQL read-only query tool for deep support diagnostics.
- Uses the main test DB user with write rights revoked for simplicity.

## Read-Only SQL Guardrails

For `supabase/sql_readonly`, use:
- main test DB user (no separate role required)
- `default_transaction_read_only=on`
- schema `USAGE` and table `SELECT` only
- no write grants, no privileged function execution
- query timeout and idle transaction timeout

Example hardening in a test environment:

```sql
-- Use your main test user (example: app_user)
ALTER ROLE app_user SET default_transaction_read_only = on;

-- Remove write capabilities on existing tables in target schema(s)
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
ON ALL TABLES IN SCHEMA public
FROM app_user;

-- Keep read path
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_user;

-- Apply defaults for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES FROM app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO app_user;
```

## Test Categories (Support + Technical Depth)

1. Auth and Session Issues
- User-facing: login/session failures.
- Technical depth: provider errors, token lifecycle, revoke/refresh path.

2. Access and Authorization Issues
- User-facing: 403/permission denied flows.
- Technical depth: policy evaluation path and role/claim mismatches.

3. Functions Runtime Failures
- User-facing: operation fails/intermittent errors.
- Technical depth: failure signatures, runtime version, correlated deploy changes.

4. Performance and Timeout Regressions
- User-facing: slow APIs/screens.
- Technical depth: heavy query windows, lock/latency patterns, saturation signals.

5. Configuration Drift
- User-facing: sudden post-change breakage.
- Technical depth: config/secret/flag diff across windows.

6. Metadata / Schema Drift
- User-facing: post-release contract breakage.
- Technical depth: DDL/migration/index/constraint change impact.

## Supabase-Only Starter Playbooks

The following playbooks are for the Supabase test environment only.
Tool selectors intentionally use the `supabase/*` namespace.

### 1) `incident_support_supabase` (case class: `incident`)
Required steps:
- `supabase/log_scan`
- `supabase/function_runs`

Suggested steps:
- `supabase/access_path_explain`
- `supabase/metadata_api_inspect`

Goal:
- identify dominant failure signature, affected runtime component, and policy/config contributors.

### 2) `billing_support_supabase` (case class: `billing`)
Required steps:
- `supabase/sql_readonly`

Suggested steps:
- `supabase/function_runs`
- `supabase/log_scan`

Goal:
- identify dominant spend/usage driver and associated technical contributors.

### 3) `general_support_supabase` (case class: `general`)
Required steps:
- `supabase/log_scan`

Suggested steps:
- `supabase/auth_timeline`
- `supabase/access_path_explain`
- `supabase/metadata_api_inspect`

Goal:
- establish first high-signal diagnosis path and narrow the failure domain quickly.

## Execution Model

1. Preload Supabase test datasets and Eleos playbooks.
2. Run objective-driven investigations through Eleos.
3. Score outcomes:
- evidence quality and relevance
- tool call efficiency (avoid redundant calls)
- diagnostic correctness (expected root-cause class)
- actionability of follow-ups/escalation guidance

## Decision

Supabase is the first standardized E2E environment for Eleos testing.
Additional environments can be added later using the same MCP contract pattern.
