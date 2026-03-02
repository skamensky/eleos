# statelyai/agent

Status: Deep dive draft (pending)
Source: https://github.com/statelyai/agent
Date: 2026-02-25

## 1) What It Is (Generic)
- A state-machine-guided agent framework built on XState.
- Uses typed observations, decisions, insights, feedback, and messages as agent memory.
- Treats decision policy as pluggable strategy (tool policy, chain-of-thought policy, shortest-path policy).

## 2) Core Strategies Observed
- Explicit environment model via state machine; decisions are constrained to valid transitions/events.
- Decision policies are separate modules, enabling controlled strategy swaps without changing core loop.
- Structured memory model stores observations/decisions/feedback/insights as typed objects with IDs/timestamps.
- `expert.interact(...)` captures transitions continuously and can auto-decide next events.
- Tool routing is derived from valid transitions (`getToolMap`) rather than free-form tool exposure.
- Bounded decision attempts (`maxAttempts`) prevent uncontrolled retry loops.

## 3) Requirement Mapping (`R1-R8`)
| Requirement | Score (0-3) | Notes |
|---|---:|---|
| `R1` Goal loop | 2 | Goal-driven decisions exist with bounded retries, but no full investigative lifecycle loop. |
| `R2` Dynamic task graph | 2 | Uses machine transitions/paths; dynamic, but bounded by predefined machine structure. |
| `R3` Evidence ledger | 2 | Strong typed memory artifacts (observations/feedback/insights), though not evidence-confidence by default. |
| `R4` Controlled exploration | 1 | Has max attempts and optional cost/path policies; lacks budgets/novelty/EV gating. |
| `R5` Termination criteria | 1 | Relies on machine/process flow; no built-in confidence/completeness termination contract. |
| `R6` Tool routing/control | 2 | Good action allowlisting via transition-derived tool map. |
| `R7` Meandering control | 1 | Some anti-drift structure from state machine/policies, no competing-hypothesis manager. |
| `R8` Multi-role architecture | 1 | Strategy separation exists, but not explicit Router/Planner/Executor/Critic role stack. |

## 4) Borrowable Ideas
- Model the investigation domain as explicit state transitions and only expose valid next actions.
- Store all runtime cognition in typed records (observation/decision/feedback/insight) instead of free-form notes.
- Make decision strategy pluggable so you can test policies without changing agent state contracts.
- Use transition-derived tool allowlists to reduce unsafe/irrelevant tool calls.

## 5) Gaps vs Our Needs
- No first-class hypothesis graph tied to evidence confidence deltas.
- No mandatory-playbook enforcement or policy-grade tool governance layer.
- No explicit budget/novelty/expected-value branch controls.

## 6) Transfer Risk
- Medium: strong conceptual patterns, but repository appears experimental/early and not directly production control-plane ready.

## 7) Verdict
- Status: `Watch`
- Reason: Valuable policy/state ideas for agent cognition design, but less complete for production investigative control and governance.

## 8) Evidence References
- `src/expert.ts`
- `src/types.ts`
- `src/decide.ts`
- `src/policies/toolPolicy.ts`
- `src/policies/chainOfThoughtPolicy.ts`
- `src/policies/shortestPathPolicy.ts`
- `src/middleware.ts`
