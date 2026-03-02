# Evidence-Led Execution for Operational Support (ELEOS) Reference Architecture Spec

Last updated: 2026-03-01
Status: Draft for implementation
Audience: Single end-to-end implementation owner

## Traceability Convention
- `Ixx` IDs refer to confirmed ideas in `brainstorm.md`.
- `Qxx` IDs refer to decision questions in `docs/spec/spec-creation-guide.md`.
- Trace tags appear per section to make requirement/design provenance explicit.
- Decision IDs (`FB-*`) refer to accepted persistent decisions in `feedback-overrides.md`.

## Decision Override Precedence
- Accepted decisions in `feedback-overrides.md` override conflicting draft wording in this spec.
- Active decision: `FB-004` (replace tool governance/authorization with playbook tool enforcement).
- Active decision: `FB-003` (remove replay/resume/checkpoint feature from runtime scope).
- Active decision: `FB-005` (classification categories are config-driven and classifier output is constrained to configured IDs).
- Active decision: `FB-006` (planner consumes category tool guidance and bounded evidence history).
- Active decision: `FB-007` (normalized persistence with link tables for relationships).
- Active decision: `FB-008` (summary-first evidence flow with explicit raw-detail escalation threshold).
- Active decision: `FB-009` (MCP-only tool integrations via explicit config).
- Active decision: `FB-010` (generic tool output payload persistence).
- Active decision: `FB-011` (configurable OpenAI-compatible base URL for proxy/non-lock-in support).

## Table of Contents
- [1. Objective](#1-objective)
- [2. Scope and Non-Goals](#2-scope-and-non-goals)
- [3. Baseline Context](#3-baseline-context)
- [4. Architectural Principles (Normative)](#4-architectural-principles-normative)
- [5. High-Level Architecture](#5-high-level-architecture)
- [6. Runtime Control Loop](#6-runtime-control-loop)
- [7. State Model Requirements](#7-state-model-requirements)
- [8. Core Data Contracts (Logical)](#8-core-data-contracts-logical)
- [9. Tool Routing and Playbook Control](#9-tool-routing-and-playbook-control)
- [10. Termination Model](#10-termination-model)
- [11. Output Contract (Selected)](#11-output-contract-selected)
- [12. Observability Contract (Selected)](#12-observability-contract-selected)
- [13. Requirement Traceability Matrix](#13-requirement-traceability-matrix)
- [14. Considering and Rejected Ideas (Context)](#14-considering-and-rejected-ideas-context)
- [15. Open Implementation Decisions](#15-open-implementation-decisions)
- [16. Source Index (Deep-Dive Anchors)](#16-source-index-deep-dive-anchors)

## 1. Objective
Design a fully autonomous investigative agent architecture that upgrades the current one-shot support investigation flow into a goal-driven, evidence-led, bounded investigation system.

This architecture must satisfy all required capabilities in one version:
- goal-driven planning loop
- dynamic task graph
- evidence ledger
- controlled exploration
- composable termination criteria
- tool routing/control
- meandering control via hypotheses
- multi-role architecture

Primary requirement source: `docs/spec/requirements.md`.
Trace: `Q1,Q3,Q7`.

## 2. Scope and Non-Goals
In scope:
- Autonomous runtime architecture and control loop
- State and evidence model constraints
- Tool enforcement and routing
- Output and observability contracts
- Requirement-to-design traceability

Non-goals:
- Model fine-tuning/training
- UI/dashboard implementation
- Organizational workflow policy
- Compliance program design
- Cost optimization strategy
- Rollout/phasing plan
- Evaluation framework design
Trace: `Q6,Q18,Q22`.

## 3. Baseline Context
Plausible baseline deployment context: an enterprise support organization with existing ticket/wiki retrieval, heterogeneous operational tools, and a first-pass classifier/planner that handles simple requests well.

Primary gap (to close): the system does not persistently pursue objectives with adaptive tasking, hypothesis updates, and bounded iterative control.
Trace: `Q17`.

## 4. Architectural Principles (Normative)
1. The runtime **must** be fully autonomous by default (no HITL dependency in the core loop).
2. The runtime **must** execute as an iterative investigation, not a single-pass response.
3. Completion **must** be decided by composable conditions, not by max-iterations alone ([AutoGen termination model](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/base/_termination.py), [termination conditions](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/conditions/_terminations.py)).
4. State **must** be separated across concerns (case, hypotheses, tasks, tool executions), while exact enums remain implementation-defined.
5. Every substantial claim in final output **must** trace to evidence artifacts.
6. Tool use **must** support playbook-driven enforcement for required steps (especially in `mandatory` mode), while preserving autonomy in `suggestive` mode.
7. Timeout is the primary hard budget control; default 2 hours, configurable.
8. Inter-step context transfer **must** be summary-first, with explicit on-demand raw artifact retrieval from durable storage when deeper evidence inspection is needed.
Trace: `I01,I02,I03,I04,I06,I07` and `Q7,Q9,Q15`.

## 5. High-Level Architecture
## 5.1 Runtime Roles
- `Router`: classifies request + binds playbook mode (mandatory/suggestive).
- `Planner`: initializes and updates competing hypotheses + task queue.
- `Executor`: performs tool calls and records artifacts.
- `Critic` (meta-cognitive loop): evaluates drift, novelty, and loop risk; triggers re-plan.
- `Reporter`: produces structured final output with citations.

This separation follows multi-role patterns from AutoGen teams/runtime ([group manager patterns](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_base_group_chat_manager.py), [runtime routing](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-core/src/autogen_core/_agent_runtime.py)).
Trace: `I03,I06` and `Q7`.

## 5.2 Core Subsystems
- `Config-Driven Classification Layer`: defines case categories and category-level tool references (`required`/`suggested`) from runtime config.
- `Case Contract Builder`: builds runtime case contract from objective + constraints.
- `Hypothesis Engine`: maintains competing hypotheses and confidence updates.
- `Task Graph Orchestrator`: mutable queue/graph of tasks tied to hypotheses.
- `Playbook Tool Enforcement Layer`: forces required-step tool use when mandatory checks remain unresolved in `mandatory` mode.
- `MCP Tool Integration Layer`: executes tools through configured MCP servers only, with deterministic route resolution from config.
- `Playbook Registry`: stores versioned, user-editable playbooks and exposes latest effective version to runtime.
- `Evidence Ledger`: typed, append-only artifact records with confidence impact.
- `Context Transfer Layer`: emits compact step summaries and resolves raw artifact drill-down reads on demand.
- `Termination Engine`: composable stop conditions.
- `DB Runtime State Layer`: typed Postgres-backed runtime state APIs for case/hypothesis/task/evidence/tool/cognition/termination/final-report access, with case-scoped row locking for mutable transitions.
Trace: `I03,I05,I06,I07` and `Q14,Q15,Q25,Q26`.

## 6. Runtime Control Loop
Two operating modes share one architecture:
- `deep_investigation` (default): full hypothesis competition + critique + completeness checks.
- `fast_mode`: serial execution of initial playbook path with reduced hypothesis invalidation/critique overhead.

Both modes remain autonomous and evidence-citing.
Trace: `I01,I03,I06` and `Q8,Q13`.

### 6.1 Pseudocode (Reference)
```text
initialize_case(request):
  case = create_case(request)
  case_class = router.classify(request, classification_config.categories)
  playbook = playbook_registry.resolve_latest_effective(case_class)
  case_contract = build_case_contract(
    case, case_class, playbook
  )
  hypotheses = seed_hypotheses(case_contract)
  task_graph = seed_tasks(case_contract, hypotheses)
  case.timeout_at = now + timeout_config

while True:
  termination_eval = termination_engine.evaluate(
    case, hypotheses, task_graph, case_contract.completion_conditions
  )
  observability.log_termination_snapshot(case.case_id, termination_eval)
  if termination_eval.should_stop:
    break

  next_task = task_graph.select_next_valid_task(case.state)
  if next_task is None:
    decision_log.write(case.case_id, "replan", reason="no valid next action")
    planner.replan(case, hypotheses, task_graph, case_contract)
    continue

  if not task_graph.is_hypothesis_link_valid(next_task):
    next_task = planner.repair_or_rewrite_task(next_task, hypotheses)
    continue

  ev_score = policy.compute_expected_value(next_task)
  if policy.reject_for_low_value(ev_score, next_task, case_contract.mandatory_checks):
    task_graph.mark_pruned(next_task.task_id, reason="expected_value_below_threshold")
    decision_log.write(case.case_id, "prune_task", task_id=next_task.task_id, expected_value=ev_score)
    continue

  tool_plan = enforcement.enforce_tool_plan(next_task, case_contract, case.state)
  tool_exec = tool_execution.start(next_task, tool_plan)
  result = executor.run(tool_plan)
  tool_execution.finish(tool_exec, result)

  artifact = evidence_ledger.record(
    result,
    tool_execution_id=tool_exec.tool_execution_id,
    linked_hypothesis=next_task.linked_hypothesis_id
  )
  step_summary = context_transfer.summarize(artifact)
  task_graph.attach_summary(next_task.task_id, step_summary, artifact.artifact_id)
  cognition.write_observation(case.case_id, artifact, step_summary)

  if critic.needs_raw_detail(step_summary) or planner.needs_raw_detail(step_summary):
    raw_payload = context_transfer.fetch_raw(artifact.tool_execution_id)
    evidence_ledger.attach_drilldown(artifact.artifact_id, raw_payload, reason="summary_insufficient")
    observability.log_drilldown(case.case_id, artifact.artifact_id)

  hypotheses = planner.update_hypotheses(hypotheses, artifact)
  cognition.write_decision(case.case_id, "hypothesis_update", artifact.artifact_id)
  task_graph = planner.update_tasks(task_graph, hypotheses, artifact)

  if result.failed:
    task_graph = planner.apply_failure_action(task_graph, next_task, playbook, result.error)

  critic_assessment = critic.evaluate(case, hypotheses, task_graph, recent_artifact=artifact)
  cognition.write_feedback(case.case_id, critic_assessment)
  if critic_assessment.requires_replan:
    planner.replan(case, hypotheses, task_graph, reason=critic_assessment.reason)

  if case.mode == "fast_mode":
    critic.reduce_depth()
    planner.limit_to_serial_path(task_graph, playbook)

completion_gate = termination_engine.evaluate_completion_gate(
  case_contract.mandatory_checks, evidence_ledger, hypotheses
)
reporter.generate(
  case=case,
  hypotheses=hypotheses,
  evidence_ledger=evidence_ledger,
  termination_snapshot=termination_eval,
  completion_gate_status=completion_gate,
  output_contract="OptionB",
  followup_channels=["customer_followups", "internal_support_followups"]
)
```

Design inspirations: Magentic-One progress/stall management ([orchestrator](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_orchestrator.py)); explicit task/tool lifecycle machinery ([ACP task state machine](https://github.com/humanlayer/agentcontrolplane/blob/main/acp/internal/controller/task/state_machine.go)).
Trace: `I01,I03,I04`.

## 7. State Model Requirements
Exact states are intentionally not prescribed here. The implementation must separate at least these domains:
- `CaseState`: lifecycle of a single investigation.
- `HypothesisState`: hypothesis objects, confidence scores, and evidence links.
- `TaskState`: mutable queue/graph state and dependency/priority metadata.
- `ToolExecutionState`: each tool invocation status, metadata, and artifact handles.

Minimum invariants:
1. Each task references a hypothesis (or explicitly marked exploratory with justification).
2. Each evidence artifact references producing tool execution.
3. Confidence changes are attributable to one or more artifact IDs.
4. Reporter reads only durable state + ledger, not transient model memory.
5. Every tool execution produces both a compact summary and a raw durable output handle.
6. Raw drill-down reads are explicit retrieval actions and must be logged.
7. Case/tool/hypothesis/evidence states are queryable by ID for deterministic runtime/audit retrieval workflows.
8. Runtime source of truth is Postgres-accessed typed DB APIs, not in-process state registries.
9. Persistence for runtime domain state should be strongly typed columns/tables; avoid generic JSON payload blobs by default.

Reference patterns: typed runtime status contracts ([ACP task spec/status](https://github.com/humanlayer/agentcontrolplane/blob/main/acp/api/v1alpha1/task_types.go)); transition-constrained decisions ([Stately decide/tool policy](https://github.com/statelyai/agent/blob/main/src/decide.ts), [tool policy map](https://github.com/statelyai/agent/blob/main/src/policies/toolPolicy.ts)).
Trace: `I03,I04,I05` and `Q15`.

## 8. Core Data Contracts (Logical)
Trace: `I05,I07` and `Q10`.
## 8.1 Case Contract
Required fields:
- `case_id`
- `objective`
- `mode` (`deep_investigation` | `fast_mode`)
- `playbook_policy` (`mandatory` | `suggestive`)
- `mandatory_checks` (can be initially sparse and discovered via experimentation)
- `timeout_at`
- `completion_conditions`

## 8.2 Hypothesis
Required fields:
- `hypothesis_id`
- `statement`
- `status` (`open` | `supported` | `rejected`)
- `confidence_score` (numeric)
- `evidence_for[]`
- `evidence_against[]`
- `last_updated_at`

## 8.3 Task
Required fields:
- `task_id`
- `linked_hypothesis_id`
- `intent` (what uncertainty this task reduces)
- `discriminates_between_hypotheses[]` (optional IDs this task is intended to differentiate)
- `expected_evidence`
- `expected_information_gain`
- `expected_value`
- `tool_plan`
- `status`
- `priority`
- `created_reason`

## 8.4 Evidence Record
Required fields:
- `artifact_id`
- `tool_execution_id`
- `source`
- `finding_summary`
- `anomalies[]`
- `confidence_impact`
- `novelty_signal`
- `summary_payload`
- `tool_execution_id`
- `raw_output_hash`
- `raw_output_size_bytes`
- `created_at`

This follows typed cognition/evidence record direction ([Stately types](https://github.com/statelyai/agent/blob/main/src/types.ts)).

## 8.5 Tool Execution Record
Required fields:
- `tool_execution_id`
- `tool_name`
- `status`
- `started_at`
- `finished_at`
- `duration_ms`
- `input_handle`
- `tool_execution_id`
- `summary_payload`
- `error`

## 8.6 Typed Cognition Records
Required record families (typed, ID/time-addressable):
- `observation_record`: observed state/evidence interpretation at a point in time
- `decision_record`: chosen action and rejected alternatives with reason
- `feedback_record`: post-action quality signal/reward or operator/system feedback
- `insight_record`: reusable pattern learned during investigation

Shared required fields:
- `record_id`
- `case_id`
- `timestamp`
- `linked_hypothesis_ids[]`
- `linked_artifact_ids[]`

## 8.7 Context Transfer Contract
Summary-first handoff is mandatory across roles/steps.

Default behavior:
- downstream components consume `summary_payload` only.

Drill-down behavior:
- downstream components may request full raw payload via `tool_execution_id` when summary is insufficient, contradictory, anomalous, or high-impact.

Minimum retrieval operations:
- `get_artifact_summary(artifact_id)`
- `get_artifact_raw(tool_execution_id)`

Pattern anchors:
- AutoGen tool-call summary and handoff context ([assistant agent](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py))
- graph runtime orchestration in LangGraph ([types.py](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py))
Trace: `I07`.

## 8.8 Runtime Read Access Contract
Minimum operations:
- `get_case_state(case_id)`
- `get_tool_execution(tool_execution_id)`
- `get_hypothesis_state(case_id, hypothesis_id)`
- `get_evidence_record(artifact_id)`

Operational requirements:
- operations are read-only and must not mutate runtime state.
- drill-down retrieval actions must be captured in observability logs.
Trace: `I03`.

## 9. Tool Routing and Playbook Control
Tool integrations are MCP-only and config-driven (`FB-009`):
- Runtime tools come from explicit MCP server config (`mcp_servers`), not local built-ins.
- Unknown/unconfigured tool routes fail deterministically.

Classification routing is config-driven (`FB-005`):
- Classifier agent receives possible categories from config.
- Classifier agent output schema is constrained at runtime to configured category IDs.
- Category tool references (`required`/`suggested`) must validate against configured MCP servers/tools.
- Classifier prompts must remain category-agnostic; categories come from config payload, not hardcoded prompt literals.

## 9.1 Routing Flow
1. Classify request.
2. Resolve latest effective playbook for case type.
3. Apply playbook policy (`mandatory` or `suggestive`).
4. Force required-step task/tool selection when mandatory checks remain unresolved.
5. Execute selected tool plans, with mandatory-step forcing when policy requires.

Trace decision: `FB-004`.

## 9.2 Playbook Policy Semantics
- `mandatory`: exact steps/order enforced; agent behaves as executor.
- `suggestive`: playbook seeds initial hypotheses/tasks; planner may adapt.

## 9.3 Mandatory Check Enforcement
- `mandatory_checks` unresolved => no terminal success state.
- mandatory checks bypass low-value pruning but remain timeout-bound.
- completion gate must include explicit pass/fail status for each mandatory check.
Trace: `I04,I06` and `Q13`.

## 9.4 Parallelism
- Parallel branch execution is off by default.
- Any future parallelism requires explicit coordination design to prevent duplicate work (consideration source: [ACP distributed locking](https://github.com/humanlayer/agentcontrolplane/blob/main/acp/docs/distributed-locking.md)).
Trace: `I04,I06` and `Q13,Q16`.

## 9.5 Playbook Structure Contract
Playbooks must be structured, versioned objects that are user-editable and runtime-executable.

Required top-level fields:
- `playbook_id`
- `version`
- `title`
- `status` (`draft` | `active` | `retired`)
- `enforcement_mode` (`suggestive` | `mandatory`)
- `applicable_case_classes[]`
- `objective_template`
- `steps[]`
- `created_by`
- `updated_at`

Required step fields:
- `step_id`
- `name`
- `goal`
- `tool_selector`
- `required` (boolean)
- `order_constraint` (`sequential` | `can_skip_if_condition` | `conditional_branch`)
- `preconditions[]`
- `expected_evidence`
- `completion_check`
- `failure_action` (`retry` | `branch` | `escalate`)

Runtime semantics:
- runtime always consumes the latest effective version provided by external playbook management surfaces.
- `mandatory` playbooks constrain step order/required actions.
- `suggestive` playbooks seed hypothesis/task generation and can be adapted by planner.
Trace: `I06` and `Q14,Q25`.

## 9.6 Playbook Mining and Promotion Loop
The architecture should support compounding learning from successful investigations.

Mining flow:
1. Ingest successful runs with objective, task sequence, evidence quality, and outcome.
2. Extract normalized step patterns by case class/signature.
3. Generate candidate playbooks with support metrics (frequency, success rate, evidence completeness).
4. Present candidate playbooks for engineer review/edit.
5. Publish approved candidates as `suggestive` or `mandatory`.
6. Track post-promotion performance and allow demotion/retirement when quality regresses.

Promotion constraints:
- no direct auto-promotion to `mandatory` without engineer confirmation.
- promotion decisions must retain links to source run IDs for auditability.
Trace: `I06` and `Q26`.

## 10. Termination Model
Termination is composable and condition-based, not loop-count-only.

Minimum condition set:
- `objective_satisfied`
- `evidence_completeness_sufficient`
- `confidence_sufficient`
- `timeout_reached`
- `no_novel_signal`
- `expected_value_below_threshold`
- `escalation_required`

The engine should support logical composition (`AND`/`OR`) and capture a termination snapshot for auditability (pattern anchor: [AutoGen termination composition](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/base/_termination.py)).
Trace: `I02` and `Q9`.

## 10.1 Expected-Value Branch Policy
Each candidate task should have an explicit expected value estimate before execution.

Reference scoring shape:
- `expected_value = novelty_signal * expected_information_gain * impact_weight`

Policy:
- reject candidate tasks below threshold unless they satisfy unresolved mandatory checks.
- penalty for tasks that do not reduce uncertainty across hypotheses.
- thresholds are configurable by case class.
Trace: `I01,I05` and `Q11`.

## 11. Output Contract (Selected)
Default output contract is Option B from `docs/research/output-contract-options.md`:
- `objective`
- `final_assessment`
- `hypotheses_considered`
- `evidence_ledger_refs`
- `confidence_score`
- `confidence_label` (derived for human readers)
- `completion_gate_status`
- `citations`
- `escalation`
- `customer_followups`
- `internal_support_followups`
Trace: `I07` and `Q10,Q19`.

## 12. Observability Contract (Selected)
Default observability is Option 2 from `docs/research/observability-options.md`:
- run identity and lifecycle boundaries
- state transitions
- hypothesis confidence deltas + reasons
- evidence ledger writes
- termination snapshots
- per-tool latency/error taxonomy

Pattern anchors: [AutoGen runtime + interventions](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-core/src/autogen_core/_agent_runtime.py), [intervention handlers](https://github.com/microsoft/autogen/blob/main/python/packages/autogen-core/src/autogen_core/_intervention.py), [LangGraph durable state](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py).
Trace: `I03,I05` and `Q20`.

## 13. Requirement Traceability Matrix
| Requirement | Architecture Elements | Confirmed Ideas Applied |
|---|---|---|
| R1 Goal-driven loop | Case contract, planner, critic, iterative control loop | I01, I03, I06 |
| R2 Dynamic task graph | Mutable task graph orchestrator + replan path | I03, I04, I06 |
| R3 Evidence ledger | Typed evidence records + summary-first handoff + raw drill-down retrieval | I05, I07 |
| R4 Controlled exploration | Critic anti-drift checks + timeout + novelty + expected-value gating | I01, I02 |
| R5 Termination criteria | Composable termination engine + timeout and escalation paths | I02 |
| R6 Tool routing/control | Classification + playbook policy + mandatory-step tool enforcement + playbook structure contract | I04, I06 |
| R7 Meandering control | Competing hypotheses + explicit differentiation intent + uncertainty/EV gating | I01, I05 |
| R8 Multi-role architecture | Router/Planner/Executor/Critic/Reporter split | I03, I06 |
Trace: `Q24`.

## 14. Considering and Rejected Ideas (Context)
## 14.1 Considering (not required baseline)
- Separate reasoning and tool-execution state machines (I16): potentially cleaner but can overcomplicate early implementation.
- Parallel coordination (I17): useful only if parallel branches are enabled.
- Fast-response mode (I18): included as an operating mode; depth reduction is policy-level, not a separate architecture.

## 14.2 Rejected (for this architecture)
- Human approval workflow states (I20): rejected because baseline is full autonomy.
- Permission matrix/hook modes as primary architecture concerns (I21, I22): permissioning handled elsewhere.
- Candidate-filtered next-actor selection (I23): rejected to preserve flexible next-action selection under playbook/state constraints.
Trace: `Q4,Q5`.

## 15. Open Implementation Decisions
Intentionally left open for implementation owner:
- exact state enum design and transition tables
- confidence calibration and label mapping thresholds
- per-case evidence completeness definitions
- future criteria for safely enabling parallel execution
- mining quality thresholds and promotion criteria for candidate playbooks
Trace: `Q11,Q15,Q16,Q26`.

## 16. Source Index (Deep-Dive Anchors)
- AutoGen: termination, orchestrators, runtime
  - https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/base/_termination.py
  - https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/conditions/_terminations.py
  - https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_orchestrator.py
  - https://github.com/microsoft/autogen/blob/main/python/packages/autogen-core/src/autogen_core/_agent_runtime.py
  - https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/agents/_assistant_agent.py
  - https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_graph/_digraph_group_chat.py
- LangGraph: graph runtime orchestration
  - https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py
- AgentControlPlane: typed resource state and task lifecycle
  - https://github.com/humanlayer/agentcontrolplane/blob/main/acp/api/v1alpha1/task_types.go
  - https://github.com/humanlayer/agentcontrolplane/blob/main/acp/internal/controller/task/state_machine.go
  - https://github.com/humanlayer/agentcontrolplane/blob/main/acp/docs/distributed-locking.md
- Stately Agent: constrained decisions and typed cognition records
  - https://github.com/statelyai/agent/blob/main/src/decide.ts
  - https://github.com/statelyai/agent/blob/main/src/policies/toolPolicy.ts
  - https://github.com/statelyai/agent/blob/main/src/types.ts
- Decision register
  - `feedback-overrides.md` (`FB-001`, `FB-002`, `FB-003`, `FB-004`, `FB-005`, `FB-006`, `FB-007`, `FB-008`, `FB-009`, `FB-010`, `FB-011`)
