# Decision Register (Persistent)

Purpose: preserve only the currently approved, durable decisions independent of git history.

Scope rule: this file is the single source of retained decision memory. Decisions not listed here are intentionally out of scope for memory retention.

## FB-001: Explainability Is A First-Class Citizen
Date: 2026-03-02
Status: Accepted

Decision:
- Explainability is a first-class architectural and product principle.
- The system must support clear explanation from high-level outcome to deep technical evidence.

Commit-level detail:
- `cc79482`: README updated to explicitly state explainability as first-class.
- `7d78151`: final case-review UX presents layered explanation paths (outcome context, loop story, decision table, on-demand tool I/O drill-down).

Why this is kept:
- It is a core product differentiator and constrains both data model and UI design.

## FB-002: Progressive Complexity Is The Preferred Narrative UX
Date: 2026-03-02
Status: Accepted

Decision:
- Case review UX should default to concise, high-signal views and reveal deeper detail on demand.

Commit-level detail:
- `d48fe7b`: introduced hybrid case-review flow with story-first brief, collapsed loop summaries, decision rail, and optional tool I/O drawer.
- `7d78151`: removed competing experimental views and made a single final case-review path the source of truth.

Why this is kept:
- It governs how technical users consume investigation traces without overload.

## FB-003: Remove Replay/Resume/Checkpoint Runtime Feature
Date: 2026-02-28
Status: Accepted

Decision:
- Runtime does not support replay/resume/checkpoint APIs.
- Investigation execution remains single-pass per run, while durable state persists in Postgres for auditability.

Commit-level detail:
- `f70973d`:
  - deleted `src/gia/core/replay_access.py`.
  - removed graph checkpointer (`InMemorySaver`) and state-history/resume APIs from graph app.
  - removed `checkpoint_every_step` runtime config.
  - removed replay wiring from runtime.

Why this is kept:
- Removes non-essential complexity from core execution while preserving auditable persistence.

## FB-004: Replace Tool Governance With Playbook Tool Enforcement
Date: 2026-02-27
Status: Accepted

Decision:
- Runtime must not rely on per-case tool allowlists as the primary control.
- Enforcement is playbook-driven:
  - `suggestive`: planner has freedom, playbook guides.
  - `mandatory`: required playbook steps/tools are forced while unresolved mandatory checks remain.

Commit-level detail:
- `288ac5f`:
  - replaced governance module with `playbook_enforcement`.
  - removed router allowlist resolution path.
  - added required-task forcing logic in graph node selection flow.
  - updated architecture spec terminology from governance/authorization to playbook tool enforcement.

Why this is kept:
- Aligns control behavior with product intent: deterministic when required, autonomous otherwise.

## FB-005: Classification Is Config-Driven With Required/Suggested Tool Arrays
Date: 2026-03-01
Status: Accepted

Decision:
- Categories are runtime configuration, not hardcoded literals.
- Each category can define:
  - `required_tool_references`
  - `suggested_tool_references`
- Classifier output must be schema-constrained to configured category IDs.
- Category/tool references must validate against configured MCP servers/tools.

Commit-level detail:
- `3ea8663`:
  - added classification config models and validators.
  - added required/suggested tool arrays per category.
  - switched classifier to runtime-generated constrained output model (`Literal[...]` via dynamic Pydantic model).
  - added config-level validation for category tool references.
- `8a3e0dd`:
  - made classifier prompt category-agnostic and config-fed.
  - added category tool guidance fields to planner input views.

Why this is kept:
- Enables deployment-specific taxonomies and policy without code changes.

## FB-006: Planner Must Use Category Tool Guidance And Bounded Evidence History
Date: 2026-03-01
Status: Accepted

Decision:
- Planner decisions (follow-up/replan) must consume category tool guidance.
- Follow-up planning must include bounded prior evidence history to reduce redundant actions.

Commit-level detail:
- `8a3e0dd`:
  - follow-up/replan prompts updated to respect required/suggested category tool guidance.
- `bb310cf`:
  - added `recent_evidence_history` to follow-up input.
  - bounded evidence history with limits (`max_items=30`, `max_summary_bytes=4000`).
  - prompt updated to avoid duplicate low-value tool calls.
- `7d181d2`:
  - moved category guidance assembly from DB view layer into planner core to keep DB views focused on data shaping.

Why this is kept:
- Improves planning quality, reduces churn, and preserves separation of concerns.

## FB-007: Persist Investigation Relationships Through Normalized Link Tables
Date: 2026-02-28
Status: Accepted

Decision:
- Relationship-heavy runtime data must be persisted via normalized link tables, not embedded arrays on primary rows.

Commit-level detail:
- `98d0d61`:
  - migration introduces link tables including:
    - `hypothesis_evidence_links`
    - `task_hypothesis_links`
    - `task_evidence_links`
    - `cognition_hypothesis_links`
    - `cognition_evidence_links`
    - `case_final_report_evidence_links`
    - `case_final_report_hypothesis_links`
  - removed multiple denormalized array/link fields from core tables.
  - updated persistence code paths to write/read explicit links.
- `1706c64`:
  - added `list_hypothesis_ids(case_id)` DB query shape and used it directly in planner linking.

Why this is kept:
- Supports strict traceability and cleaner query semantics for reasoning/audit relationships.

## FB-008: Summary-First Evidence Flow With Explicit Raw-Detail Escalation Threshold
Date: 2026-02-28
Status: Accepted

Decision:
- Default downstream reasoning should use concise evidence summaries.
- Raw-detail retrieval is on-demand and cost-aware, with explicit threshold guidance.
- For large payloads (`original_char_count > 10000`), raw fetch requires stronger expected value.

Commit-level detail:
- `c7db320`:
  - added `original_char_count` capture from raw payload.
  - exposed this signal in summary payload and raw-detail prompt guidance.
- `2a614b0`:
  - added explicit 10k-character threshold guidance to raw-detail prompt.
- `7ead6e8`:
  - simplified evidence summary representation to avoid duplicate summary fields.
  - raw-detail decision now uses direct summary-level evidence fields (`finding_summary`, `original_char_count`, `confidence_impact`, `novelty_signal`).

Why this is kept:
- Preserves deep-inspection capability while controlling cost and noise.

## FB-009: MCP-Only Tool Integration With Explicit Config-Driven Routing
Date: 2026-03-01
Status: Accepted

Decision:
- Runtime tools are MCP-only.
- Routing is deterministic from explicit MCP configuration.
- No built-in local tool fallbacks.

Commit-level detail:
- `f7df170`:
  - replaced local tool handlers with `McpToolRegistry`.
  - introduced structured MCP server/transport config and deterministic route resolution (`server_id/tool_name`, prefix routes, optional unscoped route when uniquely allowed).
  - unknown/unconfigured tool routes fail deterministically.
- `e3ee52b`:
  - added dynamic tool catalog support and Supabase-first E2E stack.
  - expanded MCP execution flow and config surface for practical environment-driven integration.

Why this is kept:
- Keeps Eleos pluggable, vendor-neutral, and predictable across deployments.

## FB-010: Persist Raw Tool Outputs As Generic Payloads
Date: 2026-02-28
Status: Accepted

Decision:
- Raw tool outputs are persisted in a generic JSON payload contract (not provider-specific typed columns per tool).
- Persistence keying is by execution identity (`tool_execution_id`) with case scoping.

Commit-level detail:
- `0a84a11`:
  - introduced `ToolOutputRow.payload_json` (`JSONB`) for raw tool outputs.
  - added DB save/read paths for raw payload by tool execution.
  - retained generic payload approach through branding/refactor transition to `eleos`.

Why this is kept:
- Enables rapid tool evolution without frequent schema churn for each tool/provider shape.

## FB-011: Support OpenAI-Compatible LLM Base URL For Proxy/Non-Lock-In Deployments
Date: 2026-03-01
Status: Accepted

Decision:
- LLM base URL is configurable.
- Runtime must support OpenAI-compatible proxy/gateway deployments (for example, LiteLLM-like proxies) to reduce provider lock-in.

Commit-level detail:
- `49cf3fe`:
  - added `ELEOS_LLM__BASE_URL` setting with OpenAI default.
  - wired structured agent model resolution through configurable OpenAI provider base URL.
  - documented gateway support in README (OpenAI-compatible endpoint, e.g. LiteLLM).

Why this is kept:
- Decouples runtime from a single provider endpoint and supports enterprise proxy topologies.
