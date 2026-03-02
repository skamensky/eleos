# Brainstorm Notes (Unified Register)

Status: Single source of truth for idea status and provenance.
Last updated: 2026-02-26

## Why this exists
Collect and triage architectural ideas for the operational investigative agent, with explicit status and source anchors.

## Status Key
- `Confirmed`: Accepted direction.
- `Considering`: Interesting, pending design tradeoff.
- `Evaluate`: Valid candidate, not yet decided.
- `Parked`: Keep noted, not active.
- `Rejected`: Intentionally not in scope for current architecture.

## Provenance Key
- `Direct`: Pattern is explicitly implemented in source repository code/docs.
- `Adapted`: Source has a close pattern; our version is a constrained adaptation.
- `Inference`: Product/design synthesis from multiple sources; not directly implemented as-is.

## Source Backfill Scope
- `I08-I15` were ideation-first entries before deep dives.
- Source anchors for these entries were backfilled from cloned deep-dive repositories on `2026-02-25`.
- `I25-I31` were added from the `openai/codex` deep dive on `2026-02-26`.

## Idea Register (Single Source of Truth)
| ID | Idea | Status | Provenance | Notes | Source Anchors |
|---|---|---|---|---|---|
| I01 | Meta-cognitive anti-drift loop | Confirmed | Direct | Separate oversight loop that checks progress/looping/distraction and triggers correction. | `microsoft/autogen`: `python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_orchestrator.py` |
| I02 | Composable completion conditions | Confirmed | Direct | Completion is a composition (evidence/confidence/budget/escalation), not max-loop only. | `microsoft/autogen`: `python/packages/autogen-agentchat/src/autogen_agentchat/base/_termination.py`, `python/packages/autogen-agentchat/src/autogen_agentchat/conditions/_terminations.py` |
| I03 | Explicit lifecycle + execution state | Confirmed | Direct | Track case lifecycle and tool execution with resume/replay first-class. | `humanlayer/agentcontrolplane`: `acp/api/v1alpha1/task_types.go`, `acp/internal/controller/task/state_machine.go`; `langchain-ai/langgraph`: `libs/langgraph/langgraph/types.py`; `microsoft/autogen`: `python/packages/autogen-core/src/autogen_core/_agent_runtime.py` |
| I04 | State-valid/playbook-valid next actions | Confirmed | Adapted | Constrain next actions by current state/playbook contracts. | `statelyai/agent`: `src/decide.ts`, `src/policies/toolPolicy.ts`; `langchain-ai/langgraph`: `libs/langgraph/langgraph/types.py` (`Command`, `Send`) |
| I05 | Typed investigative memory records | Confirmed | Direct | Observations/decisions/feedback/insights/evidence modeled as typed records with IDs/timestamps. | `statelyai/agent`: `src/types.ts`, `src/expert.ts`; `humanlayer/agentcontrolplane`: `acp/api/v1alpha1/task_types.go` |
| I06 | Standardized investigation execution pipeline + user-managed playbooks | Confirmed | Inference | Keep a standard execution pipeline and make playbooks discoverable/editable by users. | `IBM/mcp-context-forge`: `mcpgateway/services/tool_service.py` (phase-oriented tool invoke pipeline); `microsoft/autogen`: `python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_graph/_digraph_group_chat.py` |
| I07 | Context-preserving handoffs with summary + drill-down | Confirmed | Adapted | Handoffs carry compact context by default; receiving agent can fetch full raw artifacts from durable storage when needed. | `microsoft/autogen`: `python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py`; `langchain-ai/langgraph`: `libs/langgraph/langgraph/types.py` (checkpointing semantics) |
| I08 | Declarative case contract | Evaluate | Adapted | Structured case object for objective/hypotheses/allowed tools/mandatory checks/completion gate. | `humanlayer/agentcontrolplane`: `acp/api/v1alpha1/task_types.go` (`TaskSpec`/`TaskStatus` contract); `microsoft/autogen`: `.../_magentic_one_orchestrator.py`; `.../_termination.py` |
| I09 | Durable shared state document | Evaluate | Direct | Single durable case state for progress, cost, evidence, and continuity. | `langchain-ai/langgraph`: `libs/langgraph/langgraph/types.py` (`Checkpointer`/durability); `microsoft/autogen`: `python/packages/autogen-core/src/autogen_core/_agent_runtime.py` (`save_state`/`load_state`) |
| I10 | Message-driven routing | Evaluate | Direct | Route via explicit message passing/pub-sub rather than hidden control flow. | `microsoft/autogen`: `python/packages/autogen-core/src/autogen_core/_agent_runtime.py`, `_topic.py`, `_type_subscription.py` |
| I11 | Strict role separation | Evaluate | Adapted | Clear boundaries across router/planner/executor/critic/reporter. | `microsoft/autogen`: layered runtime/team split; `humanlayer/agentcontrolplane`: typed controllers/resources (`acp/internal/controller/*`, `acp/api/v1alpha1/*`) |
| I12 | Completion gate | Evaluate | Direct | Block "done" until objective checks pass and blockers are accounted for. | `microsoft/autogen`: `TerminationCondition` composition in `_termination.py`; application in `_base_group_chat_manager.py` |
| I13 | Consensus for critical checks | Evaluate | Direct | Use multi-agent review/debate patterns for high-stakes judgments. | `microsoft/autogen`: `python/docs/src/user-guide/core-user-guide/design-patterns/multi-agent-debate.ipynb`, `reflection.ipynb` |
| I14 | Continuous trigger mode | Evaluate | Adapted | Re-run on new evidence/scheduled triggers/event signals. | `humanlayer/agentcontrolplane`: reconciler/state machine loop in `acp/internal/controller/task/state_machine.go`; `microsoft/autogen`: publish-subscribe runtime in `autogen_core/_agent_runtime.py` |
| I15 | Retrospective learning loop | Evaluate | Adapted | Mine prior runs to improve future playbooks and outcomes. | `microsoft/autogen`: `python/samples/task_centric_memory/README.md`, `eval_self_teaching.py`; `statelyai/agent`: `readme.md` (feedback/insights model) |
| I16 | Separate state machines for reasoning vs tool execution | Considering | Direct | Potentially strong, but risk of overengineering; a single generic state machine may be enough. | `humanlayer/agentcontrolplane`: separate `Task` and `ToolCall` lifecycles (`task_types.go`, `acp/internal/controller/toolcall/state_machine.go`) |
| I17 | Parallel-work coordination to avoid duplicate effort | Considering | Direct | Needed if parallel branches are enabled; optional otherwise. | `humanlayer/agentcontrolplane`: lock strategy in `acp/internal/controller/task/state_machine.go`, `acp/docs/distributed-locking.md` |
| I18 | Optional fast-response mode | Considering | Adapted | Quick-answer mode with shallower depth/bounds for user speed preference. | `IBM/mcp-context-forge`: `direct_proxy` flow in `mcpgateway/services/tool_service.py`; `microsoft/autogen`: bounded loop via `max_tool_iterations` in `_assistant_agent.py` |
| I19 | Graph-native completion semantics | Parked | Adapted | Keep for later; not active design priority. | `microsoft/autogen`: graph completion behavior in `.../_graph/_digraph_group_chat.py` |
| I20 | Human approval as explicit workflow states | Rejected | Direct | Not needed for current fully autonomous target mode. | `humanlayer/agentcontrolplane`: `acp/api/v1alpha1/toolcall_types.go`, `acp/internal/controller/toolcall/state_machine.go` |
| I21 | Fail-closed route permission matrix | Rejected | Direct | Permissioning handled in another layer. | `IBM/mcp-context-forge`: `mcpgateway/middleware/token_scoping.py`, `mcpgateway/auth.py` |
| I22 | Hook policy modes (`enforce`/`permissive`/`disabled`) | Rejected | Direct | Not needed in this form for current architecture. | `IBM/mcp-context-forge`: `plugins/config.yaml`, `mcpgateway/plugins/framework/manager.py` |
| I23 | Candidate-filtered next-actor selection | Rejected | Direct | Prefer full next-action flexibility; control comes from discovered playbooks. | `microsoft/autogen`: `python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_selector_group_chat.py` |
| I24 | Runtime intervention hooks on messages/tool calls | Evaluate | Direct | Middleware can inspect/modify/block/log runtime traffic independent of planner prompts. | `microsoft/autogen`: `python/packages/autogen-core/src/autogen_core/_intervention.py`; `IBM/mcp-context-forge`: `mcpgateway/plugins/framework/manager.py` |
| I25 | Dual durability with indexed replay + read-repair | Evaluate | Direct | Keep immutable run artifacts plus query-optimized state index and reconciliation/backfill for resilient resume/replay. | `openai/codex`: `codex-rs/core/src/rollout/recorder.rs`, `codex-rs/core/src/state_db.rs`, `codex-rs/core/tests/suite/resume.rs` |
| I26 | Tiered persistence modes for investigations | Considering | Direct | Support compact default persistence and richer forensic mode without changing orchestration logic. | `openai/codex`: `codex-rs/core/src/rollout/policy.rs` |
| I27 | Capability-gated parallel tool execution | Considering | Direct | Enable parallelism only for explicitly parallel-safe tools; otherwise enforce exclusive execution. | `openai/codex`: `codex-rs/core/src/tools/parallel.rs`, `codex-rs/core/tests/suite/tool_parallelism.rs` |
| I28 | Self-testing policy rules (`match` / `not_match`) | Evaluate | Direct | Treat governance rules as testable objects to prevent silent drift in command/network policy behavior. | `openai/codex`: `codex-rs/execpolicy/README.md`, `codex-rs/execpolicy/src/rule.rs`, `codex-rs/core/tests/suite/exec_policy.rs` |
| I29 | Delegation guardrails for sub-agents | Evaluate | Direct | Bound delegation with spawn budgets/depth limits and explicit parent-child completion notifications. | `openai/codex`: `codex-rs/core/src/agent/control.rs`, `codex-rs/core/src/agent/guards.rs` |
| I30 | Boundary-aware context compaction | Evaluate | Direct | Preserve semantic ordering when summarizing long threads by reinjecting compaction boundaries explicitly. | `openai/codex`: `codex-rs/core/src/compact.rs`, `codex-rs/core/src/compact_remote.rs` |
| I31 | Two-phase memory mining pipeline | Considering | Direct | Use parallel per-run extraction plus serialized global consolidation to mine successful runs into reusable playbook knowledge. | `openai/codex`: `codex-rs/core/src/memories/README.md`, `codex-rs/core/src/memory_trace.rs` |

## Gaps to Solve for Our Use Case
- First-class hypothesis objects and confidence updates.
- Evidence ledger schema per artifact/tool call.
- Budget/novelty/expected-value controls as explicit policy.
- Domain router mapping issue classes to mandatory checks (IAM, audit logs, networking, etc.).

## Open Questions
- What is the minimum viable state schema?
- Which case classes require mandatory tool checks?
- How should confidence be computed and explained?
- What are safe default budgets by case type?
