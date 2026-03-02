# py-why/pywhyllm

Status: Deep dive draft (pending)
Source: https://github.com/py-why/pywhyllm
Date: 2026-03-02

## 1) What It Is (Generic)
- A causal-analysis helper library that uses LLM prompts to suggest causal structure candidates.
- Focused on "suggester" APIs: pairwise direction, confounders, mediators, IVs, latent confounders, negative controls, and graph critique.
- Positioned as augmentation for the broader PyWhy ecosystem (especially DoWhy workflows), not as an orchestration/runtime system.

## 2) Core Strategies Observed
- Prompt-driven causal heuristics:
  - LLM outputs are parsed via tag extraction (for example `<answer>`, `<confounding_factor>`) rather than strict schema-enforced structured outputs.
- Domain-expert simulation:
  - Prompts explicitly role-play domain experts and aggregate repeated suggestions/counters.
- RAG branch for pairwise causality:
  - `AugmentedModelSuggester` downloads/queries CauseNet and combines lexical + embedding retrieval before asking the model.
- Thin protocol layer:
  - Protocols define conceptual interfaces (`ModelerProtocol`, `IdentifierProtocol`) but implementation is mostly direct prompt methods.
- Notebook-first workflow:
  - Repository emphasizes examples and exploratory notebook usage over production runtime/ops design.

## 3) Requirement Mapping (`R1-R8`)
| Requirement | Score (0-3) | Notes |
|---|---:|---|
| `R1` Goal loop | 1 | Supports iterative suggestion calls, but no autonomous objective loop. |
| `R2` Dynamic task graph | 0 | No task graph/runtime scheduler. |
| `R3` Evidence ledger | 0 | No durable evidence ledger or citation lifecycle. |
| `R4` Controlled exploration | 1 | Some repeated querying/heuristic filtering, but no formal EV/novelty/budget controls. |
| `R5` Termination criteria | 0 | No composable termination engine for case execution. |
| `R6` Tool routing/control | 0 | No tool registry/router/policy layer. |
| `R7` Meandering control | 2 | Good causal-structure primitives (confounders/mediators/IV/critique) relevant to hypothesis discipline. |
| `R8` Multi-role architecture | 1 | "Multi-role" exists as prompt role-play, not runtime role orchestration. |

## 4) Borrowable Ideas
- Causal-specific reasoning primitives:
  - Backdoor, mediator, IV, and negative-control suggestion APIs can inspire specialized Eleos agents/tools.
- CauseNet-backed retrieval idea:
  - Pre-LLM retrieval over causal knowledge graph priors can improve precision for directional hypotheses.
- Expert-ensemble pattern:
  - "Multiple domain expert" synthesis can be adapted to Eleos as structured, typed ensemble criticing for risky decisions.

## 5) Gaps vs Our Needs
- Not a production control-plane:
  - No case runtime orchestration, no graph execution loop, no playbook enforcement, no MCP tool lifecycle.
- Weak output contracts for your standards:
  - Relies on regex/tag parsing and free-form prompts rather than strict typed schemas (Pydantic/native structured output).
- Limited persistence/observability:
  - No durable DB-backed state history for investigations, decisions, and evidence traceability.
- Partial API surface:
  - Some interfaces are placeholders/TODOs (for example `suggest_frontdoor`).

## 6) Transfer Risk
- Moderate for direct adoption:
  - Architectural mismatch with Eleos runtime and type-safety standards.
- Low-to-moderate for idea borrowing:
  - Causal primitives and retrieval heuristics are useful if re-implemented with Eleos typed-agent patterns.

## 7) Verdict
- Status: `Watch`
- Reason:
  - Valuable as a causal-reasoning idea source and optional specialized capability layer.
  - Not suitable as a foundational runtime/orchestration dependency for Eleos.

## 8) Evidence References
- `pywhyllm/suggesters/model_suggester.py`
- `pywhyllm/suggesters/identification_suggester.py`
- `pywhyllm/suggesters/validation_suggester.py`
- `pywhyllm/suggesters/augmented_model_suggester.py`
- `pywhyllm/utils/augmented_model_suggester_utils.py`
- `pywhyllm/protocols/modeler.py`
- `pywhyllm/protocols/identifier.py`
- `README.md`
