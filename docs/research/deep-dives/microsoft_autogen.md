# microsoft/autogen

Status: Deep dive draft (pending)
Source: https://github.com/microsoft/autogen
Date: 2026-02-25

## 1) What It Is (Generic)
- A layered multi-agent framework with a low-level event/runtime core and higher-level team/orchestration APIs.
- Supports multiple orchestration styles (round-robin, selector, swarm handoffs, graph flows, Magentic-One orchestration).
- Provides composable termination, state save/load, and tool-use loops with configurable limits.

## 2) Core Strategies Observed
- Runtime-first architecture: typed agents, topics/subscriptions, and message routing in `autogen-core`.
- Group chat manager abstraction centralizes turn handling, speaker selection, and termination signaling.
- Rich termination stack: composable `AND/OR` conditions across message count, token usage, timeout, handoff, content checks, external signals.
- Graph-based execution (`GraphFlow`) supports DAG/conditional/looped flows with explicit cycle safeguards.
- Tool loop controls in assistant agent: `max_tool_iterations`, optional reflection, handoff-aware tool execution.
- Magentic-One orchestrator uses ledger-style planning/facts/progress checks plus stall detection and re-planning.
- Runtime intervention handlers can modify/log/drop messages before send/publish/response.

## 3) Requirement Mapping (`R1-R8`)
| Requirement | Score (0-3) | Notes |
|---|---:|---|
| `R1` Goal loop | 3 | Strong orchestration loops, especially with Magentic-One and team managers. |
| `R2` Dynamic task graph | 3 | GraphFlow + selector/swarm patterns provide robust dynamic branching/routing options. |
| `R3` Evidence ledger | 2 | Maintains structured threads/state and Magentic-style ledgers, but not full evidence-confidence schema by default. |
| `R4` Controlled exploration | 3 | Strong controls: max turns/messages/tokens/time, max tool iterations, stall-based replan hooks. |
| `R5` Termination criteria | 3 | Best-in-class composable termination conditions and explicit reset semantics. |
| `R6` Tool routing/control | 2 | Good tool registration/loops/handoffs + runtime intervention hooks; strict policy catalog still needs layering. |
| `R7` Meandering control | 2 | Stall/loop detection and progress checks exist (Magentic-One), but no explicit competing-hypothesis framework. |
| `R8` Multi-role architecture | 3 | Strong role-oriented architecture via teams/orchestrators/agents and layered runtime responsibilities. |

## 4) Borrowable Ideas
- Build termination as composable stateful conditions, not a single max-loop variable.
- Separate runtime messaging/orchestration primitives from high-level agent UX APIs.
- Add graph execution mode for deterministic playbooks with conditional branches and joins.
- Add explicit stall detection + re-plan pathway when progress is not being made.
- Use intervention hooks in runtime to enforce policy/logging/drop logic independent of prompts.

## 5) Gaps vs Our Needs
- No native hypothesis competition/evidence-confidence calculus.
- Needs domain policy layer for mandatory cloud case checks and tool governance hard rules.
- Token/time/turn controls are present, but novelty and expected-value branch scoring are not first-class.

## 6) Transfer Risk
- Moderate: broad, powerful stack with many abstractions; careful scoping needed to avoid over-adoption.
- Lower conceptual risk due mature patterns and clear separation of responsibilities.

## 7) Verdict
- Status: `Keep`
- Reason: Strongest direct source of reusable orchestration/termination patterns for your target requirements.

## 8) Evidence References
- `python/packages/autogen-agentchat/src/autogen_agentchat/base/_termination.py`
- `python/packages/autogen-agentchat/src/autogen_agentchat/conditions/_terminations.py`
- `python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_base_group_chat_manager.py`
- `python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_graph/_digraph_group_chat.py`
- `python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_orchestrator.py`
- `python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py`
- `python/packages/autogen-core/src/autogen_core/_intervention.py`
- `python/packages/autogen-core/src/autogen_core/_single_threaded_agent_runtime.py`
