# facebookresearch/HyperAgents

Status: Deep dive draft (pending)
Source: https://github.com/facebookresearch/HyperAgents
Date: 2026-03-26

## 1) What It Is (Generic)
- A self-referential self-improvement framework that evolves a combined task-agent and meta-agent codebase over generations.
- Core runtime is an archive-based outer loop: select a parent agent, let it edit itself, evaluate the child, and keep the resulting lineage artifacts.
- Released repository is both a reference implementation of DGM-Hyperagents and an experiment harness across coding, paper review, robotics reward design, game environments, and Olympiad grading.

## 2) Core Strategies Observed
- Self-referential architecture: `task_agent.py` and `meta_agent.py` live in the same editable program, so future generations can modify both task behavior and the improvement procedure itself.
- Open-ended archive search: the system maintains `archive.jsonl`, parent-child metadata, lineage patch replay, and score-based parent selection to preserve stepping stones instead of greedily overwriting the current best agent.
- Staged evaluation: cheap early evaluations gate whether a child earns more expensive full evaluation, reducing wasted compute on weak variants.
- Patch-lineage reconstruction: each generation stores prior and current diff files, and descendants are recreated by replaying cumulative patches inside fresh containers.
- Sandbox-first execution: meta-agent edits and downstream evaluations run inside disposable Docker containers with explicit timeouts and repository reset/clean steps.
- Minimal initial agent surface: the baseline hyperagent starts with extremely small prompts and only two tools (`bash`, `editor`), intentionally leaving a wide search space for later generations to improve.
- Paper-reported meta-improvements are separate from the baseline snapshot: the paper shows evolved additions like persistent memory, performance tracking, evaluation analysis, and compute-aware planning, but those are examples from experiment runs rather than stable primitives in the initial released code.
- Parent selection is split between stronger and weaker paths: `select_parent(...)` uses score plus child-count penalties, while the editable `select_next_parent.py` currently reduces to random valid-parent sampling despite the paper describing a more novelty-aware mechanism.

## 3) Requirement Mapping (`R1-R8`)
| Requirement | Score (0-3) | Notes |
|---|---:|---|
| `R1` Goal loop | 2 | Strong iterative outer loop for benchmark improvement, but objective is population-level score optimization rather than case-level investigation. |
| `R2` Dynamic task graph | 1 | Has a branching generation tree/archive, not a first-class within-case task graph or hypothesis graph. |
| `R3` Evidence ledger | 1 | Stores reports, patches, chat histories, and metadata per generation, but lacks structured evidence/confidence semantics. |
| `R4` Controlled exploration | 2 | Good exploration controls via staged eval, child-count penalties, archive branching, and timeouts; no explicit EV/novelty budget framework in the released runtime. |
| `R5` Termination criteria | 1 | Mostly bounded by `max_generation`, tool/runtime timeouts, and staged-eval gating; no completeness or confidence-based stop condition. |
| `R6` Tool routing/control | 1 | Fixed minimal toolset plus Docker isolation exists, but routing/governance is prompt-driven rather than policy-driven. |
| `R7` Meandering control | 1 | Archive stepping stones and anti-overexploitation penalties help macro-level exploration, but there is no competing-hypothesis discipline. |
| `R8` Multi-role architecture | 2 | Clear task-agent/meta-agent split plus separate evaluation/selection harness, but not the richer Router/Planner/Executor/Critic/Reporter stack. |

## 4) Borrowable Ideas
- Preserve an archive of intermediate variants instead of always replacing the current best system.
- Use staged evaluation to cheaply filter weak branches before paying for full assessment.
- Persist parent links, patches, metadata, and evaluation outputs so every improvement path is reconstructable.
- Keep the initial agent simple enough that later generations can invent their own analysis and memory tooling.
- Bias exploration away from overused parents to reduce premature convergence while still favoring strong performers.
- Treat paper-reported meta-improvements as overlays learned during search, not assumptions that must exist in the baseline runtime.

## 5) Gaps vs Our Needs
- No first-class hypothesis graph, evidence ledger, or confidence-delta model.
- No playbook-driven mandatory checks or MCP-native routing/policy layer.
- No investigation-oriented role stack for router/planner/executor/critic/reporter behavior.
- Termination is benchmark-budget centric, not evidence-completeness centric.
- Explainability is limited to logs, patches, and reports rather than layered human-readable investigation narratives.
- Several of the most interesting capabilities in the paper (persistent memory, performance tracking, richer evaluation analysis) are demonstrated as evolved outcomes, not stable primitives in the released baseline code.

## 6) Transfer Risk
- High domain mismatch: the core loop is long-horizon evolutionary benchmark optimization, not a single-run evidence-led investigation workflow.
- Medium implementation risk: archive/patch/container patterns are reusable, but copying the full framework would import long feedback cycles and substantial evaluation complexity.
- Medium evidence risk: some of the strongest ideas come from paper-reported evolved agents, so direct reproducibility from the baseline snapshot is unclear.

## 7) Verdict
- Status: `Watch`
- Reason: High-signal source for open-ended exploration, stepping-stone search, staged evaluation, and meta-improvement ideas, but weak direct fit for Eleos-style evidence-led investigations and too much of the best behavior lives outside the baseline runtime.

## 8) Evidence References
- `README.md`
- `generate_loop.py`
- `meta_agent.py`
- `task_agent.py`
- `run_meta_agent.py`
- `run_task_agent.py`
- `select_next_parent.py`
- `ensemble.py`
- `agent/base_agent.py`
- `agent/llm.py`
- `agent/llm_withtools.py`
- `agent/tools/bash.py`
- `agent/tools/edit.py`
- `utils/gl_utils.py`
- `utils/domain_utils.py`
- `domains/harness.py`
- `domains/report.py`
- `arXiv:2603.19461` (Sections 3-5, Appendix A, Appendix E, Section 6)
- `https://ai.meta.com/research/publications/hyperagents/`
