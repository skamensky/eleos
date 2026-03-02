# openai/codex

Status: Deep dive draft (pending)
Source: https://github.com/openai/codex
Date: 2026-02-26

## 1) What It Is (Generic)
- A terminal-first coding-agent runtime with explicit tool orchestration, sandbox/approval controls, and multi-agent delegation.
- Combines append-only rollout logs with optional SQLite indexing/backfill for resume, replay, and queryability.
- Implements policy-governed execution (command/network) and mode-specific behavior (`default`, `plan`) with structured UI-facing events.

## 2) Core Strategies Observed
- Dual durability surfaces: raw JSONL rollout as source artifact + SQLite state mirror for indexed queries and repair/backfill.
- Tiered persistence policy for runtime events (`limited` vs `extended`) to balance replay fidelity vs storage/noise.
- Capability-aware tool parallelism: tools marked parallel-safe run concurrently; non-safe tools take exclusive lock.
- Sub-agent control-plane guards: max thread limits, depth limits, reservation/cleanup semantics, parent completion notifications.
- Policy-as-code for command/network governance: prefix/network rules, strictest-decision resolution, and load-time `match`/`not_match` validation.
- Structured planning signals as events (`update_plan`, plan deltas/completions) separate from execution mode.
- Context compaction with boundary-aware reinjection to preserve semantic ordering and recover from long-thread drift.
- Two-phase memory mining pipeline: parallel per-run extraction + serialized global consolidation with leases and watermarking.

## 3) Requirement Mapping (`R1-R8`)
| Requirement | Score (0-3) | Notes |
|---|---:|---|
| `R1` Goal loop | 2 | Strong iterative turn/runtime loop, but no native incident objective contract/hypothesis model. |
| `R2` Dynamic task graph | 2 | Supports plan updates, sub-agents, and parallel tool calls; not a first-class hypothesis-task graph. |
| `R3` Evidence ledger | 3 | Strong durable event/item history + indexed metadata with resume/replay/read-repair patterns. |
| `R4` Controlled exploration | 3 | Strong operational controls (sandboxing, approvals, exec policy, timeouts, parallel locks, quotas). |
| `R5` Termination criteria | 2 | Turn/task completion states exist; objective/evidence-completeness termination is not native. |
| `R6` Tool routing/control | 3 | Rich tool catalog construction, mode constraints, MCP routing, and policy-gated command execution. |
| `R7` Meandering control | 1 | No explicit competing-hypothesis uncertainty reduction loop. |
| `R8` Multi-role architecture | 3 | Clear role/mode split and robust sub-agent lifecycle/control patterns. |

## 4) Borrowable Ideas
- Use dual durability: immutable raw run artifacts plus query-optimized state index with reconciliation.
- Add persistence tiers so default investigations keep compact replay-critical events and opt into richer forensic mode when needed.
- Treat policy rules as testable objects (`match`/`not_match`) to reduce silent guardrail drift.
- Gate tool parallelism by capability instead of all-or-nothing parallel execution.
- Add explicit sub-agent spawn budgets and parent-child completion notifications to prevent runaway delegation.
- Keep plan artifacts as structured events independent of natural-language responses.
- Implement summary compaction with explicit reinjection boundaries so summaries do not break downstream context semantics.

## 5) Gaps vs Our Needs
- No native hypothesis object lifecycle with explicit evidence-for/evidence-against confidence deltas.
- No native case-type completion gates tied to domain mandatory checks (IAM/network/logs).
- No native expected-value/novelty scoring for branch generation/pruning.
- Primarily coding-workflow optimized; incident investigation contracts must be layered.

## 6) Transfer Risk
- Moderate: many patterns are highly reusable, but domain mismatch can cause overfitting to coding-agent assumptions.
- Moderate implementation complexity: substantial runtime surface area; selective borrowing is safer than framework-level adoption.

## 7) Verdict
- Status: `Keep`
- Reason: High-signal operational patterns for durability, governance, delegation, and context management that directly strengthen investigative-agent production architecture.

## 8) Evidence References
- `codex-rs/core/src/agent/control.rs`
- `codex-rs/core/src/agent/guards.rs`
- `codex-rs/core/src/tools/parallel.rs`
- `codex-rs/core/src/tools/router.rs`
- `codex-rs/core/src/tools/handlers/plan.rs`
- `codex-rs/core/src/rollout/policy.rs`
- `codex-rs/core/src/rollout/recorder.rs`
- `codex-rs/core/src/state_db.rs`
- `codex-rs/core/src/state/session.rs`
- `codex-rs/core/src/compact.rs`
- `codex-rs/core/src/compact_remote.rs`
- `codex-rs/core/src/memories/README.md`
- `codex-rs/execpolicy/README.md`
- `codex-rs/execpolicy/src/policy.rs`
- `codex-rs/execpolicy/src/rule.rs`
- `shell-tool-mcp/README.md`
