# Reference Architecture Spec Creation Guide

Last updated: 2026-02-25
Status: Approved guidance for authoring the high-level reference architecture spec.

## Purpose
This guide captures stakeholder decisions made before drafting the final reference architecture spec. It is an evidence trail so future readers understand what was intentionally chosen, what was intentionally excluded, and what remains open for implementation detail.

## Canonical IDs (Do Not Reassign)
Idea IDs:
- Confirmed ideas currently in scope: `I01` `I02` `I03` `I04` `I05` `I06` `I07` (source: `brainstorm.md`)
- Non-confirmed ideas remain tracked in `brainstorm.md` and must retain existing IDs when referenced.

Question IDs:
- Decision questions in this guide map to `Q1` through `Q26` in order.
- `Q1 == question 1`, `Q2 == question 2`, ... `Q26 == question 26`.
- Zero-padded forms (e.g., `Q01`) are allowed aliases but should not replace canonical IDs.
- If questions are added later, append (`Q27+`); never renumber existing IDs.

## Regeneration Guardrails
When regenerating the reference architecture spec from this guide:
- Preserve all existing `Ixx` and `Qxx` references.
- Keep a one-to-one mapping between the numbered decision log questions and `Qxx` IDs.
- Do not drop confirmed idea IDs from trace tags even if content is refactored.
- If an idea or question is superseded, mark it superseded and map to replacement ID; do not recycle IDs.

## Primary Document Type (Chosen)
- Create a **Reference Architecture Spec**.
- It must be concise and information-dense, while preserving critical implementation guidance and design intent.
- It must include brief rationale sections for `Considering` and `Rejected` ideas to preserve architectural spirit.

## Audience
- Primary audience is a single highly capable implementation owner ("10x" engineer) who can execute end-to-end.
- Assume strong architectural and agentic systems literacy.

## Scope and Non-Goals
In scope:
- Architecture for a fully autonomous investigative agent framework.
- How confirmed ideas satisfy requirements.
- Operational control loop, state design constraints, tool governance, termination model, and evidence model.

Explicit non-goals:
- Model fine-tuning/training strategy.
- UI/dashboard design details.
- Organizational process design.
- Compliance/security program design (PII policies, retention policy, residency policy).
- Cost optimization and phased rollout planning.
- Formal evaluation framework design for LLM quality (may be a separate future project).

## Final Decision Log (Question Context + Decisions + Rejected Alternatives)

1. **Question:** What should this document be called, and who is the primary audience?  
**Decision:** Use a **Reference Architecture Spec** for one highly capable end-to-end implementor.  
**Alternatives considered/rejected:** RFC+ADR bundle, implementation blueprint, and narrative synthesis were considered; rejected as primary format because the goal is one canonical architecture template with source-linked traceability.

2. **Question:** What is the target horizon: MVP in weeks, or full production design?  
**Decision:** Do not include timelines or phased delivery estimates.  
**Alternatives considered/rejected:** MVP-vs-production scheduling framing rejected for this document.

3. **Question:** Which requirements are absolute must for v1 vs later?  
**Decision:** No version split. Treat all requirements as part of one complete target architecture.  
**Alternatives considered/rejected:** Must-have/later partitioning rejected.

4. **Question:** Should the spec include only confirmed ideas, or also considering ideas as optional variants?  
**Decision:** Confirmed ideas are implementation guidance; considering ideas appear briefly for design spirit/context.  
**Alternatives considered/rejected:** Pure confirmed-only narrative rejected because it loses context.

5. **Question:** For rejected ideas, include short rationale only, or rejected + revisit criteria?  
**Decision:** Include concise rationale for rejected ideas.  
**Alternatives considered/rejected:** Formal revisit criteria deferred to future governance docs.

6. **Question:** What is explicitly out of scope for this spec?  
**Decision:** Keep scope architecture-focused for autonomous investigative control-plane behavior.  
**Alternatives considered/rejected:** Including model fine-tuning, UI/product process, compliance program, and rollout economics rejected for this spec.

7. **Question:** What autonomy level is required at launch?  
**Decision:** Full autonomy only.  
**Alternatives considered/rejected:** Configurable manual/HITL mode rejected for baseline architecture.

8. **Question:** Should one architecture support both fast mode and deep investigation mode?  
**Decision:** Yes.  
**Alternatives considered/rejected:** Deep-only architecture rejected. Fast mode should run a simpler serial path with reduced critique/hypothesis invalidation.

9. **Question:** What are hard budgets/SLAs (latency, tool calls, cost, timeout)?  
**Decision:** Timeout is the only hard control in this spec; default initial timeout is 2 hours and configurable.  
**Alternatives considered/rejected:** Hard limits on latency, tool-count, and cost are deferred; not primary constraints now.

10. **Question:** How should confidence be represented (numeric, banded, or both)?  
**Decision:** Store numeric confidence.  
**Alternatives considered/rejected:** Persisting labels/bands as primary confidence rejected; labels should be derived at render time for humans.

11. **Question:** What minimum evidence is required before final answer by case type?  
**Decision:** Leave concrete thresholds/checklists to implementation experimentation.  
**Alternatives considered/rejected:** Fixed global checklist in this guide rejected as premature.

12. **Question:** Formal hypothesis model in initial implementation, or lighter model first?  
**Decision:** Full formal hypothesis model from the start.  
**Alternatives considered/rejected:** Lighter hypothesis mode rejected.

13. **Question:** Should playbooks be strictly enforced, suggestive, or mixed?  
**Decision:** Mixed.  
**Alternatives considered/rejected:** Strict-only and suggestive-only both rejected. If user marks steps/order mandatory, agent is executor; otherwise playbook is suggestive seed.

14. **Question:** Who can create/edit playbooks, and what approval/versioning model should exist?  
**Decision:** Assume playbook is supplied as latest effective version from external UI/workflow.  
**Alternatives considered/rejected:** Defining authoring governance/version lifecycle in this spec rejected as out of scope.

15. **Question:** Desired state model granularity: single case state machine or separate case/tool/hypothesis states?  
**Decision:** Require separated state domains across concerns.  
**Alternatives considered/rejected:** Single monolithic state rejected for baseline. Exact state enums/transitions remain implementation-defined.

16. **Question:** Parallelism in initial architecture, and if yes how aggressive?  
**Decision:** Parallel execution off by default.  
**Alternatives considered/rejected:** Aggressive parallel branch execution rejected for now due quality risk; implementor may override with strong evidence.

17. **Question:** Required integrations at launch (tool classes/APIs)?  
**Decision:** Use current system capabilities as baseline integration set.  
**Alternatives considered/rejected:** New mandatory external tool classes beyond current baseline are not required by this guide.

18. **Question:** Compliance/security constraints to encode?  
**Decision:** Treat as non-goal in this spec.  
**Alternatives considered/rejected:** Embedding compliance program requirements in this architecture doc rejected.

19. **Question:** What output contract do end users need?  
**Decision:** Choose Option B from `docs/research/output-contract-options.md`, with two follow-up channels: `customer_followups` and `internal_support_followups`.  
**Alternatives considered/rejected:** Option A rejected as default due limited rigor; Option C rejected as default due complexity (can remain optional).

20. **Question:** What observability is mandatory?  
**Decision:** Choose Option 2 from `docs/research/observability-options.md` as default.  
**Alternatives considered/rejected:** Option 1 rejected as insufficient for debugging; Option 3 rejected as default due higher complexity.

21. **Question:** What rollout strategy should be documented (shadow/canary/phased)?  
**Decision:** Assume full rollout context for a new project.  
**Alternatives considered/rejected:** Shadow/canary/phased rollout planning omitted from this spec.

22. **Question:** What evaluation framework should be in the spec?  
**Decision:** Exclude evaluation framework design from this spec.  
**Alternatives considered/rejected:** Full evaluation framework (offline replay/goldens/KPIs/LLM evals) deferred to separate project.

23. **Question:** Preferred document style: concise or comprehensive?  
**Decision:** Concise and information-dense, without losing critical implementation guidance.  
**Alternatives considered/rejected:** Very long comprehensive format rejected as default.

24. **Question:** Source links inline, appendix, or both?  
**Decision:** Inline citations in relevant design sections.  
**Alternatives considered/rejected:** Appendix-only traceability rejected.

25. **Question:** What structure must a playbook have so it is editable by users and executable by the agent?  
**Decision:** Playbooks must be structured, versioned objects with explicit step contracts and execution semantics.  
**Alternatives considered/rejected:** Prompt-only freeform playbooks rejected because they are hard to validate, diff, mine, and enforce.

26. **Question:** Should the architecture include playbook mining from successful runs and promotion to mandatory playbooks?  
**Decision:** Yes. The architecture should support mining successful runs into candidate playbooks, with engineer review/edit before promotion to suggestive or mandatory status.  
**Alternatives considered/rejected:** Manual-only playbook authoring rejected as it misses compounding learning from production investigations.

## Required Inputs for Spec Author
Use these documents as primary inputs:
- `docs/spec/requirements.md`
- `brainstorm.md` (single source of idea status and provenance)
- `docs/research/repo-tracking.md` (repo landscape and mapping)
- `docs/research/output-contract-options.md` (selected: Option B)
- `docs/research/observability-options.md` (selected: Option 2)

Baseline use-case motivation should be domain-generic (for example: enterprise support investigations spanning logs, identity/access, configuration, and data APIs), not tied to one organization.

## Mandatory Spec Properties
The final reference architecture spec must:
- Map every requirement to concrete architecture elements.
- Show how each confirmed idea contributes to requirement satisfaction.
- Include `Ixx` and `Qxx` trace tags so each section can be traced back to idea and decision sources.
- Include brief sections for considering/rejected ideas and rationale.
- Enforce full autonomy as baseline behavior.
- Include timeout-driven termination controls.
- Require separated state domains (without over-prescribing exact enums in this guide).
- Include inline source anchors so readers can deep-dive into external implementations.
- Define a concrete playbook structure contract (editable and executable).
- Define a playbook mining/promotion lifecycle from successful runs to reviewed reusable playbooks.

## Open Implementation Questions (Intentionally Left Open)
- Exact state machine definitions and transitions for each separated state domain.
- Exact confidence calibration function and mapping thresholds.
- Exact case-type evidence completeness criteria.
- Conditions under which parallelism can be safely enabled later.
- Mining quality thresholds and promotion criteria for candidate playbooks.

## Evidence Trail Notes
This guide consolidates the decision discussion and follow-up clarifications, and aligns them with selected options in:
- `docs/research/output-contract-options.md`
- `docs/research/observability-options.md`
