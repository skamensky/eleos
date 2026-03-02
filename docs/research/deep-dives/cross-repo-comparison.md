# Cross-Repo Comparison (Draft)

Status: Draft comparison (pending)
Date: 2026-03-02

## Current High-Signal Set
- `langchain-ai/langgraph` (`Keep`)
- `humanlayer/agentcontrolplane` (`Keep`)
- `IBM/mcp-context-forge` (`Keep`)
- `statelyai/agent` (`Watch`)
- `microsoft/autogen` (`Keep`)
- `openai/codex` (`Keep`)
- `py-why/pywhyllm` (`Watch`)

## Fast Ranking by Requirement Fit
1. `microsoft/autogen`
- Best overall for orchestration + termination + multi-role execution patterns.

2. `langchain-ai/langgraph`
- Best low-level state-graph + durable execution substrate.

3. `humanlayer/agentcontrolplane`
- Best control-plane durability + tool-call lifecycle + HITL state transitions.

4. `openai/codex`
- Best operational coding-agent patterns for durable rollouts, command governance, sub-agent controls, and capability-gated parallel tool runtime.

5. `IBM/mcp-context-forge`
- Best tool governance and policy gateway patterns.

6. `statelyai/agent`
- Strong cognition/state-policy concepts, less complete as production orchestration framework.

7. `py-why/pywhyllm`
- Useful causal-reasoning primitives and retrieval ideas, but not a runtime/orchestration substrate.

## Composite Pattern Stack to Borrow
- Orchestration substrate: graph/state execution (`langgraph`, `autogen`).
- Durable outer loop and task/tool state machines (`agentcontrolplane`).
- Governance shell for tool routing/auth/policy (`mcp-context-forge`).
- Operational durability/control details: rollout tiers, read-repair indexing, sub-agent budgets, and parallel-safe tool scheduling (`openai/codex`).
- Cognitive state schema (observations/decisions/feedback/insights) (`statelyai/agent`).
- Causal-structure suggestion primitives for hypothesis discipline (`pywhyllm`).

## Known Cross-Repo Gap (Still Yours to Build)
- First-class hypothesis graph + evidence ledger with confidence deltas and uncertainty reduction.
- Novelty + expected-value scoring for branch expansion/termination.
- Case-type completion contracts (mandatory IAM/network/log checks by class).
