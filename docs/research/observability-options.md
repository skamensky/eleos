# Observability Options (Basic -> Advanced)

Last updated: 2026-02-25

## Purpose
Define what telemetry and introspection to capture for a fully autonomous investigative agent.

## Option 1: Basic Run Tracking
Capture:
- `case_id`, `run_id`, start/end time, final status
- final answer + citations
- tool calls count and failure count
- timeout reason when applicable

Pros:
- Minimal overhead
- Quick operational visibility

Cons:
- Weak debugging and replay
- Limited quality diagnostics

## Option 2: Structured Investigation Telemetry (Recommended default)
Capture:
- Everything in Option 1, plus:
- state transitions (case lifecycle + task lifecycle)
- hypothesis updates (confidence deltas + reason)
- evidence ledger writes (artifact IDs, finding type, novelty signal)
- termination condition evaluation snapshots
- per-tool latency/error taxonomy

Pros:
- Strong support for debugging drift/loops
- Enables quality analysis without full raw logs everywhere

Cons:
- Requires event schema discipline

## Option 3: Replay-Grade Telemetry
Capture:
- Everything in Option 2, plus:
- full prompt/response envelopes (redacted policy-aware)
- deterministic checkpoints for resume/replay
- full tool IO handles in durable storage
- intervention/policy hook decisions with before/after payload hashes

Pros:
- Full forensic replay and model-behavior analysis
- Best for architecture hardening

Cons:
- Highest storage/security burden
- More complex governance controls

## Recommended Minimum Set
For your requirements, minimum should include:
- `run_id`/`case_id`
- lifecycle state transitions
- hypothesis confidence updates
- evidence ledger records
- termination condition snapshots
- timeout path reason

## Source Pattern Anchors
- `microsoft/autogen`: runtime and intervention hooks (`autogen_core/_agent_runtime.py`, `_intervention.py`)
- `langchain-ai/langgraph`: durable checkpoints/state (`libs/langgraph/langgraph/types.py`)
- `humanlayer/agentcontrolplane`: explicit status phases and controller events (`acp/api/v1alpha1/task_types.go`, `acp/internal/controller/task/state_machine.go`)
