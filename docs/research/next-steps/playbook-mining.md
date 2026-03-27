# Playbook Mining

Status: Promising next step
Date: 2026-03-27

Eleos already persists the right raw ingredients for cross-run learning: completed cases, task sequences, evidence quality, final reports, and cognition records. A strong next step is to mine completed investigations to surface reusable playbook candidates and promising step sequences instead of relying only on manually authored playbooks.

## 1) Mine Completed Runs
- Ingest completed runs by case class and objective shape.
- Extract executed step sequences, follow-up branches, retries, and evidence-producing paths.
- Surface recurring high-signal patterns such as:
  - step sequences that repeatedly lead to good evidence and clean completion
  - optional branches that often resolve uncertainty well
  - failure-recovery patterns that should become explicit playbook guidance

## 2) Machine Score And Rank Candidates
- Generate candidate playbooks and candidate step-sequence fragments from mined runs.
- Rank them using simple machine scoring such as:
  - support/frequency across completed runs
  - completion rate
  - evidence completeness rate
  - average confidence and novelty contribution
  - regression signals after adoption
- Prefer candidates that are both reusable and discriminative, not just common.

## 3) Human Review And Promotion
- Present mined candidates as draft playbooks or draft step additions, not active runtime policy.
- Let an operator review:
  - source runs
  - extracted sequence
  - score/support metrics
  - suggested enforcement mode (`suggestive` first by default)
- Promotion flow should be: mined candidate -> reviewed draft -> published playbook/update -> later performance tracking.

This is a promising next step because it gives Eleos a practical form of stepping-stone preservation across runs while staying aligned with the current playbook-centered architecture.
