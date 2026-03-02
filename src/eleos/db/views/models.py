from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from eleos.models.enums import HypothesisStatus, Mode, TaskStatus
from eleos.models.ids import CaseId, HypothesisId
from eleos.models.payloads import RawToolPayload
from eleos.models.report import CompletionGateStatus


class PlaybookStepView(BaseModel):
    step_id: str
    name: str
    goal: str
    tool_selector: str
    required: bool
    order_constraint: str
    preconditions: list[str] = Field(default_factory=list)
    expected_evidence: str
    completion_check: str
    failure_action: str


class PlaybookView(BaseModel):
    playbook_id: str
    version: str
    title: str
    status: str
    enforcement_mode: str
    applicable_case_classes: list[str] = Field(default_factory=list)
    objective_template: str
    created_by: str
    steps: list[PlaybookStepView] = Field(default_factory=list)


class HypothesisView(BaseModel):
    hypothesis_id: HypothesisId
    statement: str
    status: HypothesisStatus
    confidence_score: float
    last_updated_at: datetime


class TaskView(BaseModel):
    task_id: str
    linked_hypothesis_id: HypothesisId | None = None
    intent: str
    expected_evidence: str
    expected_information_gain: float
    expected_value: float
    tool_name: str
    tool_input_objective: str
    tool_input_step: str | None = None
    tool_input_reason: str | None = None
    tool_input_evidence_id: str | None = None
    status: TaskStatus
    priority: int
    created_reason: str
    updated_at: datetime


class EvidenceRecordView(BaseModel):
    evidence_id: str
    tool_execution_id: str
    source: str
    finding_summary: str
    original_char_count: int
    anomalies: list[str] = Field(default_factory=list)
    confidence_impact: float
    novelty_signal: float
    raw_output_size_bytes: int
    detail_reason: str | None = None


class MandatoryCheckView(BaseModel):
    check_id: str
    description: str


class CategoryToolGuidanceView(BaseModel):
    required_tool_references: list[str] = Field(default_factory=list)
    suggested_tool_references: list[str] = Field(default_factory=list)


class TerminationSnapshotView(BaseModel):
    loop_count: int
    objective_satisfied: bool
    evidence_completeness_sufficient: bool
    confidence_sufficient: bool
    timeout_reached: bool
    no_novel_signal: bool
    expected_value_below_threshold: bool
    escalation_required: bool
    should_stop: bool
    reason: str


class HypothesisSeedInputView(BaseModel):
    case_id: CaseId
    objective: str
    mode: Mode
    case_class: str
    playbook: PlaybookView


class TaskSeedInputView(BaseModel):
    case_id: CaseId
    objective: str
    mode: Mode
    case_class: str
    playbook: PlaybookView
    hypotheses: list[HypothesisView] = Field(default_factory=list)


class HypothesisUpdateInputView(BaseModel):
    hypotheses: list[HypothesisView] = Field(default_factory=list)
    evidence: EvidenceRecordView


class FollowupTaskInputView(BaseModel):
    objective: str
    mode: Mode
    category_tools: CategoryToolGuidanceView = Field(default_factory=CategoryToolGuidanceView)
    hypotheses: list[HypothesisView] = Field(default_factory=list)
    tasks: list[TaskView] = Field(default_factory=list)
    evidence: EvidenceRecordView
    recent_evidence_history: list[EvidenceRecordView] = Field(default_factory=list)


class ReplanTaskInputView(BaseModel):
    objective: str
    mode: Mode
    category_tools: CategoryToolGuidanceView = Field(default_factory=CategoryToolGuidanceView)
    reason: str
    hypotheses: list[HypothesisView] = Field(default_factory=list)
    tasks: list[TaskView] = Field(default_factory=list)


class RawDetailInputView(BaseModel):
    evidence: EvidenceRecordView


class TaskSelectionInputView(BaseModel):
    objective: str
    mode: Mode
    pending_tasks: list[TaskView] = Field(default_factory=list)
    unresolved_mandatory_checks: list[MandatoryCheckView] = Field(default_factory=list)
    last_novelty_signal: float | None = None
    expected_value_floor: float


class CompletionCheckInputView(BaseModel):
    check: MandatoryCheckView
    evidence_records: list[EvidenceRecordView] = Field(default_factory=list)


class CriticInputView(BaseModel):
    case_id: CaseId
    objective: str
    mode: Mode
    loop_count: int
    max_iterations: int
    novelty_floor: float
    last_novelty_signal: float | None = None
    top_confidence: float = 0.0
    hypotheses: list[HypothesisView] = Field(default_factory=list)
    tasks: list[TaskView] = Field(default_factory=list)


class ReportSynthesisInputView(BaseModel):
    objective: str
    hypotheses: list[HypothesisView] = Field(default_factory=list)
    evidence_records: list[EvidenceRecordView] = Field(default_factory=list)
    termination_snapshot: TerminationSnapshotView
    completion_gate_status: CompletionGateStatus


class ToolSummaryInputView(BaseModel):
    evidence: EvidenceRecordView
    raw_payload: RawToolPayload
