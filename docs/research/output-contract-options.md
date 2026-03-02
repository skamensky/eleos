# Output Contract Options (Basic -> Advanced)

Last updated: 2026-02-25

## Purpose
Define what the agent returns to the user at case completion, with increasing rigor.

## Option A: Basic (Fastest to adopt)
Fields:
- `answer`: direct conclusion
- `key_evidence`: 3-5 bullets
- `citations`: source links/IDs
- `next_step`: one recommended action

Pros:
- Simple and readable
- Low implementation overhead

Cons:
- Weak uncertainty signaling
- Harder to audit investigation quality

Best for:
- Early adoption and fast-mode responses

## Option B: Structured Investigative Summary (Recommended default)
Fields:
- `objective`
- `final_assessment`
- `hypotheses_considered`: each with `status` (`supported`/`rejected`/`open`) and short rationale
- `evidence_ledger_refs`: artifact IDs + short finding per artifact
- `confidence_score`: numeric confidence (e.g., `0.82`)
- `confidence_label` (optional, derived): human-readable label generated from score bands
- `completion_gate_status`: pass/fail per required check
- `citations`
- `escalation`: `none` or reason
- `customer_followups`: next actions phrased for end customer requesters
- `internal_support_followups`: privileged/internal actions for support engineers (e.g., admin checks, escalations, protected tooling)

Pros:
- Strong traceability to requirements (goal, hypotheses, evidence, termination)
- Good balance of readability and rigor

Cons:
- Slightly heavier payload
- Requires consistent evidence IDs

Best for:
- Standard deep investigation mode

## Option C: Forensic/Audit Contract (Most rigorous)
Fields:
- Everything in Option B, plus:
- `timeline`: ordered events with timestamps
- `decision_log`: key decision points + why alternatives were not chosen
- `tool_execution_log`: tool name, inputs (redacted), output handle, duration, outcome
- `policy_events`: guardrails triggered, denied branches, timeout/budget checks
- `replay_handle`: case run ID for deterministic replay

Pros:
- Maximum auditability and incident postmortem quality
- Strongest for debugging agent behavior

Cons:
- Highest implementation/storage complexity
- Can be verbose for end users

Best for:
- Critical incidents and architecture verification

## Recommendation
- Use Option B as default contract.
- Allow Option A in fast mode.
- Keep Option C available behind a `forensic_output=true` switch.
