# humanlayer/agentcontrolplane

Status: Deep dive draft (pending)
Source: https://github.com/humanlayer/agentcontrolplane
Date: 2026-02-25

## 1) What It Is (Generic)
- A Kubernetes-native agent control plane using CRDs and controllers.
- Breaks execution into typed resources (`LLM`, `Agent`, `Task`, `ToolCall`, `MCPServer`, `ContactChannel`).
- Uses reconciler state machines to progress each resource through explicit phases.

## 2) Core Strategies Observed
- Control-plane state model: each resource has explicit `spec` + `status` with phase/status/statusDetail.
- Outer-loop execution as a durable workflow: `Task` cycles through `ReadyForLLM -> ToolCallsPending -> ReadyForLLM` until final answer/failure.
- Tool execution decoupled as first-class objects: each LLM tool call becomes a `ToolCall` resource with its own lifecycle.
- Hard tool governance from config: tool availability derived from validated `Agent` dependencies (MCP servers, human channels, sub-agents).
- Human-in-the-loop as a state transition, not a prompt trick: approval/input phases and external call IDs are tracked in status.
- Concurrency/race controls: per-task mutex + Kubernetes lease-based distributed locking.
- High observability by default: status fields + Kubernetes events + trace span contexts.

## 3) Requirement Mapping (`R1-R8`)
| Requirement | Score (0-3) | Notes |
|---|---:|---|
| `R1` Goal loop | 2 | Strong operational loop for task completion, but no native hypothesis/objective semantics. |
| `R2` Dynamic task graph | 2 | Dynamic branching via created `ToolCall`/child `Task` resources; graph is event/state driven rather than arbitrary DAG. |
| `R3` Evidence ledger | 2 | Structured artifacts exist (`ContextWindow`, tool results, statuses/events), but not an explicit evidence-confidence ledger. |
| `R4` Controlled exploration | 2 | Good reliability controls (locking, retries, requeue), limited novelty/EV/budget intelligence. |
| `R5` Termination criteria | 2 | Explicit terminal phases (`FinalAnswer`/`Failed`) and tool-call completion checks; no confidence-based completeness gate. |
| `R6` Tool routing/control | 3 | Strongest area: declarative tool sources + type-based execution + approval gates + validation before use. |
| `R7` Meandering control | 1 | No competing-hypothesis manager or uncertainty-reduction policy. |
| `R8` Multi-role architecture | 3 | Clear role split at controller level (`agent`, `task`, `toolcall`, `llm`, etc.) with bounded responsibilities. |

## 4) Borrowable Ideas
- Represent investigation lifecycle as explicit phase transitions with durable status fields.
- Split "reasoning loop" and "tool execution" into separate stateful objects/workers.
- Treat human approval/input as normal tool states with auditable transitions.
- Implement concurrency controls as infra primitives (locks/leases), not prompt instructions.
- Use event + status detail logs as a built-in operational audit trail.

## 5) Gaps vs Our Needs
- No first-class hypothesis tracking with confidence deltas.
- No novelty/expected-value branch prioritization policy.
- No native evidence completeness matrix by incident category.
- Task loop is mostly conversation/tool-cycle oriented; investigation DAG semantics need an added layer.

## 6) Transfer Risk
- Medium-high: excellent control-plane patterns, but operationally heavy if copied directly (Kubernetes CRD/controller complexity).
- Moderate adaptation risk if your runtime is not k8s-native.

## 7) Verdict
- Status: `Keep`
- Reason: Strong blueprint for durable orchestration, tool governance, and HITL lifecycle management; useful even if adapted to a lighter runtime.

## 8) Evidence References
- `acp/api/v1alpha1/task_types.go`
- `acp/api/v1alpha1/toolcall_types.go`
- `acp/api/v1alpha1/agent_types.go`
- `acp/internal/controller/task/state_machine.go`
- `acp/internal/controller/toolcall/state_machine.go`
- `acp/internal/controller/toolcall/executor.go`
- `acp/docs/distributed-locking.md`
