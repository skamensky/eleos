from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from eleos.db.models import (
    CaseFinalReportCheckRow,
    CaseFinalReportEvidenceLinkRow,
    CaseFinalReportHypothesisLinkRow,
    CaseFinalReportRow,
    CaseMandatoryCheckRow,
    CaseRunRow,
    CognitionRecordRow,
    HypothesisEvidenceLinkRow,
    PlaybookStepRow,
    TerminationSnapshotRow,
    ToolExecutionRow,
    ToolOutputRow,
)
from eleos.db.views.mappers import to_hypothesis_view, to_termination_snapshot_view
from eleos.db.views.models import (
    EvidenceRecordView,
    HypothesisView,
    TaskView,
    TerminationSnapshotView,
)
from eleos.models.ids import CaseId
from eleos.models.report import CompletionGateStatus, FinalReport


class FinalReportResponse(BaseModel):
    objective: str
    final_assessment: str
    hypotheses_considered: list[HypothesisView] = Field(default_factory=list)
    evidence_ledger_refs: list[str] = Field(default_factory=list)
    confidence_score: float
    confidence_label: str
    completion_gate_status: CompletionGateStatus
    citations: list[str] = Field(default_factory=list)
    escalation: str | None
    customer_followups: list[str] = Field(default_factory=list)
    internal_support_followups: list[str] = Field(default_factory=list)
    termination_snapshot: TerminationSnapshotView


class InvestigationRunResponse(BaseModel):
    case_id: CaseId
    report: FinalReportResponse


class PlaybookStepCreateRequest(BaseModel):
    step_order: int
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


class PlaybookCreateRequest(BaseModel):
    playbook_id: str | None = None
    version: str
    title: str
    status: str
    enforcement_mode: str
    applicable_case_classes: list[str] = Field(default_factory=list)
    objective_template: str
    created_by: str
    steps: list[PlaybookStepCreateRequest] = Field(default_factory=list)


class CategoryOptionResponse(BaseModel):
    category_id: str
    description: str
    required_tool_references: list[str] = Field(default_factory=list)
    suggested_tool_references: list[str] = Field(default_factory=list)


class ToolOptionResponse(BaseModel):
    tool_name: str
    function_description: str


class PlaybookFormOptionsResponse(BaseModel):
    categories: list[CategoryOptionResponse] = Field(default_factory=list)
    tools: list[ToolOptionResponse] = Field(default_factory=list)
    enforcement_modes: list[str] = Field(default_factory=list)
    order_constraints: list[str] = Field(default_factory=list)
    failure_actions: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)


class CaseRunSummaryResponse(BaseModel):
    case_id: str
    case_class: str
    status: str
    objective: str
    mode: str
    playbook_policy: str
    loop_count: int
    timeout_at: datetime
    created_at: datetime
    updated_at: datetime


class MandatoryCheckStateResponse(BaseModel):
    check_id: str
    description: str
    passed: bool | None
    reason: str | None


class ToolExecutionResponse(BaseModel):
    tool_execution_id: str
    tool_name: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    input_handle: str
    error: str | None
    updated_at: datetime


class ToolOutputResponse(BaseModel):
    tool_execution_id: str
    tool_name: str
    payload_json: dict[str, object]
    created_at: datetime
    updated_at: datetime


class HypothesisEvidenceLinkResponse(BaseModel):
    hypothesis_id: str
    evidence_id: str
    relation: str
    created_at: datetime


class CognitionRecordResponse(BaseModel):
    record_id: str
    record_type: str
    timestamp: datetime
    decision_action: str | None
    decision_reason: str | None
    feedback_requires_replan: bool | None
    feedback_reason: str | None
    feedback_novelty_score: float | None
    feedback_drift_score: float | None
    insight_text: str | None
    linked_hypothesis_ids: list[str] = Field(default_factory=list)
    linked_evidence_ids: list[str] = Field(default_factory=list)


class FinalReportCheckResponse(BaseModel):
    check_id: str
    description: str
    passed: bool
    reason: str


class FinalReportStoredResponse(BaseModel):
    objective: str
    final_assessment: str
    confidence_score: float
    confidence_label: str
    completion_gate_passed: bool
    customer_followups: list[str] = Field(default_factory=list)
    internal_support_followups: list[str] = Field(default_factory=list)
    escalation: str | None
    termination_loop_count: int
    checks: list[FinalReportCheckResponse] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CaseRunDetailResponse(BaseModel):
    summary: CaseRunSummaryResponse
    mandatory_checks: list[MandatoryCheckStateResponse] = Field(default_factory=list)
    hypotheses: list[HypothesisView] = Field(default_factory=list)
    tasks: list[TaskView] = Field(default_factory=list)
    task_hypothesis_links: dict[str, list[str]] = Field(default_factory=dict)
    task_evidence_links: dict[str, list[str]] = Field(default_factory=dict)
    tool_executions: list[ToolExecutionResponse] = Field(default_factory=list)
    tool_outputs: list[ToolOutputResponse] = Field(default_factory=list)
    evidence_records: list[EvidenceRecordView] = Field(default_factory=list)
    hypothesis_evidence_links: list[HypothesisEvidenceLinkResponse] = Field(default_factory=list)
    cognition_records: list[CognitionRecordResponse] = Field(default_factory=list)
    termination_snapshots: list[TerminationSnapshotView] = Field(default_factory=list)
    final_report: FinalReportStoredResponse | None = None


class CaseTimelineEventType(str, Enum):
    CASE_STARTED = "case_started"
    TASK_UPSERTED = "task_upserted"
    TOOL_EXECUTION = "tool_execution"
    EVIDENCE_RECORDED = "evidence_recorded"
    COGNITION_RECORDED = "cognition_recorded"
    TERMINATION_EVALUATED = "termination_evaluated"
    FINAL_REPORT_STORED = "final_report_stored"


class CaseTimelineReferenceResponse(BaseModel):
    reference_type: str
    reference_id: str
    label: str | None = None


class CaseTimelineEventResponse(BaseModel):
    event_id: str
    event_type: CaseTimelineEventType
    occurred_at: datetime
    title: str
    summary: str
    detail: str | None = None
    caused_by_event_id: str | None = None
    references: list[CaseTimelineReferenceResponse] = Field(default_factory=list)


class CaseRunTimelineResponse(BaseModel):
    case_id: str
    objective: str
    status: str
    latest_stop_reason: str | None = None
    objective_satisfied: bool | None = None
    unresolved_blockers: list[str] = Field(default_factory=list)
    events: list[CaseTimelineEventResponse] = Field(default_factory=list)


def to_final_report_response(report: FinalReport) -> FinalReportResponse:
    return FinalReportResponse(
        objective=report.objective,
        final_assessment=report.final_assessment,
        hypotheses_considered=[to_hypothesis_view(row) for row in report.hypotheses_considered],
        evidence_ledger_refs=list(report.evidence_ledger_refs),
        confidence_score=report.confidence_score,
        confidence_label=report.confidence_label,
        completion_gate_status=report.completion_gate_status,
        citations=list(report.citations),
        escalation=report.escalation,
        customer_followups=list(report.customer_followups),
        internal_support_followups=list(report.internal_support_followups),
        termination_snapshot=to_termination_snapshot_view(report.termination_snapshot),
    )


def to_playbook_step_row(step: PlaybookStepCreateRequest, *, playbook_fk: int) -> PlaybookStepRow:
    return PlaybookStepRow(
        playbook_fk=playbook_fk,
        step_order=step.step_order,
        step_id=step.step_id,
        name=step.name,
        goal=step.goal,
        tool_selector=step.tool_selector,
        required=step.required,
        order_constraint=step.order_constraint,
        preconditions=list(step.preconditions),
        expected_evidence=step.expected_evidence,
        completion_check=step.completion_check,
        failure_action=step.failure_action,
    )


def to_case_run_summary_response(row: CaseRunRow) -> CaseRunSummaryResponse:
    return CaseRunSummaryResponse(
        case_id=row.case_id,
        case_class=row.case_class,
        status=row.status,
        objective=row.objective,
        mode=row.mode,
        playbook_policy=row.playbook_policy,
        loop_count=row.loop_count,
        timeout_at=row.timeout_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_mandatory_check_state_response(row: CaseMandatoryCheckRow) -> MandatoryCheckStateResponse:
    return MandatoryCheckStateResponse(
        check_id=row.check_id,
        description=row.description,
        passed=row.passed,
        reason=row.reason,
    )


def to_tool_execution_response(row: ToolExecutionRow) -> ToolExecutionResponse:
    return ToolExecutionResponse(
        tool_execution_id=row.tool_execution_id,
        tool_name=row.tool_name,
        status=row.status,
        started_at=row.started_at,
        finished_at=row.finished_at,
        duration_ms=row.duration_ms,
        input_handle=row.input_handle,
        error=row.error,
        updated_at=row.updated_at,
    )


def to_tool_output_response(row: ToolOutputRow) -> ToolOutputResponse:
    return ToolOutputResponse(
        tool_execution_id=row.tool_execution_id,
        tool_name=row.tool_name,
        payload_json=row.payload_json,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_hypothesis_evidence_link_response(
    row: HypothesisEvidenceLinkRow,
) -> HypothesisEvidenceLinkResponse:
    return HypothesisEvidenceLinkResponse(
        hypothesis_id=row.hypothesis_id,
        evidence_id=row.evidence_id,
        relation=row.relation,
        created_at=row.created_at,
    )


def to_cognition_record_response(
    row: CognitionRecordRow,
    *,
    linked_hypothesis_ids: list[str],
    linked_evidence_ids: list[str],
) -> CognitionRecordResponse:
    return CognitionRecordResponse(
        record_id=row.record_id,
        record_type=row.record_type,
        timestamp=row.timestamp,
        decision_action=row.decision_action,
        decision_reason=row.decision_reason,
        feedback_requires_replan=row.feedback_requires_replan,
        feedback_reason=row.feedback_reason,
        feedback_novelty_score=row.feedback_novelty_score,
        feedback_drift_score=row.feedback_drift_score,
        insight_text=row.insight_text,
        linked_hypothesis_ids=linked_hypothesis_ids,
        linked_evidence_ids=linked_evidence_ids,
    )


def to_final_report_stored_response(
    row: CaseFinalReportRow,
    *,
    checks: list[CaseFinalReportCheckRow],
    evidence_links: list[CaseFinalReportEvidenceLinkRow],
    hypothesis_links: list[CaseFinalReportHypothesisLinkRow],
) -> FinalReportStoredResponse:
    return FinalReportStoredResponse(
        objective=row.objective,
        final_assessment=row.final_assessment,
        confidence_score=row.confidence_score,
        confidence_label=row.confidence_label,
        completion_gate_passed=row.completion_gate_passed,
        customer_followups=list(row.customer_followups),
        internal_support_followups=list(row.internal_support_followups),
        escalation=row.escalation,
        termination_loop_count=row.termination_loop_count,
        checks=[
            FinalReportCheckResponse(
                check_id=check.check_id,
                description=check.description,
                passed=check.passed,
                reason=check.reason,
            )
            for check in checks
        ],
        evidence_ids=[item.evidence_id for item in evidence_links],
        hypothesis_ids=[item.hypothesis_id for item in hypothesis_links],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_termination_snapshot_views(
    rows: list[TerminationSnapshotRow],
) -> list[TerminationSnapshotView]:
    return [to_termination_snapshot_view(row) for row in rows]
