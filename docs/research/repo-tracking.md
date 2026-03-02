# Repo Tracking and Requirement Mapping (Discovery + Deep Dive)

Status: Mixed phase. P1 high-signal deep dives completed; coding-assistant runtime deep dive added.
Last updated: 2026-02-26

## Requirement Key
- `R1`: Goal-driven planning loop
- `R2`: Dynamic task graph
- `R3`: Evidence ledger
- `R4`: Controlled exploration (budget, novelty, EV)
- `R5`: Termination criteria
- `R6`: Tool routing and control
- `R7`: Meandering control with competing hypotheses
- `R8`: Multi-role architecture

## Canonical Idea Register
- Idea status/provenance is tracked only in `brainstorm.md` to avoid split lists.
- `repo-tracking.md` is now repo-discovery and requirement-fit only.

## Candidate Repos (Initial Pass)
| Repo | Why It Looks Relevant | Mapped Requirements | Shallow Signal | Deep-Dive Priority | Status |
|---|---|---|---|---|---|
| `langchain-ai/langgraph` | Graph/state orchestration, durable execution, checkpoints, HITL | `R1,R2,R5,R8` | High | P1 | Deep-dive complete (`Keep`) |
| `microsoft/autogen` | Multi-agent role patterns, handoffs, tool loops | `R1,R2,R8` | High | P1 | Deep-dive complete (`Keep`) |
| `crewAIInc/crewAI` | Crew/flow separation, event-driven orchestration concepts | `R1,R2,R8` | Medium | P2 | Candidate |
| `statelyai/agent` | Explicit state-machine policy + observations/feedback/planning | `R1,R2,R5,R7` | High | P1 | Deep-dive complete (`Watch`) |
| `humanlayer/agentcontrolplane` | Outer-loop scheduler, async tasks, human approval as tool, MCP | `R1,R2,R5,R6,R8` | High | P1 | Deep-dive complete (`Keep`) |
| `IBM/mcp-context-forge` | Gateway/governance/registry for tool routing and policy | `R6,R4` | High | P1 | Deep-dive complete (`Keep`) |
| `NVIDIA-NeMo/Guardrails` | Programmable rails for safe/controlled behavior and dialog flow | `R4,R6,R5` | Medium-High | P2 | Candidate |
| `coroot/coroot` | RCA/inspection mindset for incident triage and actionable checks | `R3,R5,R7` | Medium | P3 | Candidate |
| `AgentOps-AI/agentops` | Agent tracing, cost and run telemetry for loop/budget visibility | `R4,R5` | Medium | P3 | Candidate |
| `langfuse/langfuse` | Observability/evals for trajectories, confidence and quality feedback | `R3,R4,R5` | Medium | P3 | Candidate |
| `openai/swarm` | Lightweight handoff ideas; useful as conceptual baseline | `R8,R1` | Medium-Low | P4 | Watchlist |
| `openai/codex` | Production coding-agent control-plane patterns: tool governance, durability, delegation, compaction | `R2,R3,R4,R6,R8` | High | P1 | Deep-dive complete (`Keep`) |
| `archestra-ai/archestra` | MCP-native gateway/orchestration + security/governance angle | `R6,R4` | Medium | P2 | Candidate |

## Early Gaps (Across Repos vs Our Needs)
- No repo looked like a direct match for a first-class hypothesis/evidence ledger tied to confidence deltas (`R3`,`R7`) in an incident context.
- Many frameworks support orchestration, but fewer enforce policy-grade novelty/EV stopping logic (`R4`).
- Termination is often loop-count or task-done based; fewer provide case-type completeness contracts (`R5`).

## Deep-Dive Queue (Proposed Order)
1. `NVIDIA-NeMo/Guardrails` (optional next)
2. `crewAIInc/crewAI`
3. `archestra-ai/archestra`
4. `langfuse/langfuse`
5. `AgentOps-AI/agentops`
