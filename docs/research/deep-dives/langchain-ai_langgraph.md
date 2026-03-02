# langchain-ai/langgraph

Status: Deep dive draft (pending)
Source: https://github.com/langchain-ai/langgraph
Date: 2026-02-25

## 1) What It Is (Generic)
- A low-level orchestration framework for long-running, stateful agents/workflows.
- Core abstraction is an executable state graph (`StateGraph` -> compiled graph) with explicit nodes/edges/branches.
- Supports persistent checkpoints, interrupts, retries, streaming events, and resumable execution.

## 2) Core Strategies Observed
- Explicit state-graph execution model: node functions read/write structured shared state.
- Dynamic routing primitives: conditional edges + `Send` + `Command(goto=...)` for runtime branching.
- Durable execution: checkpointers (memory/sqlite/postgres) with thread-scoped resume/replay.
- Human-in-the-loop primitive: `interrupt()` and resume with `Command(resume=...)`.
- Control knobs for execution boundaries: `recursion_limit`, retry policy, durability mode.
- Prebuilt agent loop includes bounded step behavior (`remaining_steps`) and tool execution node patterns.

## 3) Requirement Mapping (`R1-R8`)
| Requirement | Score (0-3) | Notes |
|---|---:|---|
| `R1` Goal loop | 2 | Strong loop/orchestration substrate, but no built-in objective/hypothesis semantics. |
| `R2` Dynamic task graph | 3 | First-class branching/routing via conditional edges, `Send`, `Command.goto`. |
| `R3` Evidence ledger | 1 | Persistent state/checkpoints exist, but no native evidence-ledger schema or confidence deltas. |
| `R4` Controlled exploration | 2 | Provides guardrails like `recursion_limit`, retries, step bounds; novelty/EV not native. |
| `R5` Termination criteria | 2 | End conditions + out-of-steps detection exist; domain completeness/confidence gates must be added. |
| `R6` Tool routing/control | 2 | Tool allowlist/validation via `ToolNode`; policy-grade routing should be layered on top. |
| `R7` Meandering control | 1 | No built-in competing-hypothesis framework; can be implemented in state + critic nodes. |
| `R8` Multi-role architecture | 2 | Supports composing role-specific nodes/subgraphs, but role framework is not opinionated by default. |

## 4) Borrowable Ideas
- Use explicit graph orchestration instead of prompt-only loop control.
- Persist investigation state every step for replay/resume/audit.
- Use interrupt/resume for human approval or escalation checkpoints.
- Standardize runtime routing with `Command`/`Send`-like semantics.
- Add explicit step-limit and recursion guards as hard safety controls.

## 5) Gaps vs Our Needs
- Missing native hypothesis and evidence-ledger objects tied to confidence updates.
- Missing native novelty detection and expected-value gating for branch expansion.
- Missing case-type playbook enforcement (mandatory IAM/network/log checks) as first-class policy.
- Missing domain-specific termination contract (evidence completeness by incident class).

## 6) Transfer Risk
- Moderate: framework is general and powerful, but easy to over-flex without strict policy/state contracts.
- Moderate migration risk from prebuilt agent helpers due churn/deprecation hints around agent APIs.

## 7) Verdict
- Status: `Keep`
- Reason: Excellent orchestration substrate for `R1/R2` and durable execution controls, with manageable gaps that can be solved by layering domain policy/state schema on top.

## 8) Evidence References
- `libs/langgraph/langgraph/graph/state.py`
- `libs/langgraph/langgraph/types.py`
- `libs/langgraph/langgraph/errors.py`
- `libs/langgraph/langgraph/pregel/main.py`
- `libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py`
- `libs/prebuilt/langgraph/prebuilt/tool_node.py`
