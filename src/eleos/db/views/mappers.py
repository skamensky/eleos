from __future__ import annotations

from eleos.db.models import (
    CaseMandatoryCheckRow,
    EvidenceRecordRow,
    HypothesisRow,
    PlaybookRow,
    PlaybookStepRow,
    TaskRow,
    TerminationSnapshotRow,
)
from eleos.db.views.models import (
    EvidenceRecordView,
    HypothesisView,
    MandatoryCheckView,
    PlaybookStepView,
    PlaybookView,
    TaskView,
    TerminationSnapshotView,
)
from eleos.models.enums import HypothesisStatus, TaskStatus
from eleos.models.ids import as_hypothesis_id


def to_playbook_view(row: PlaybookRow) -> PlaybookView:
    return PlaybookView(
        playbook_id=row.playbook_id,
        version=row.version,
        title=row.title,
        status=row.status,
        enforcement_mode=row.enforcement_mode,
        applicable_case_classes=list(row.applicable_case_classes),
        objective_template=row.objective_template,
        created_by=row.created_by,
        steps=[to_playbook_step_view(step) for step in row.steps],
    )


def to_playbook_step_view(row: PlaybookStepRow) -> PlaybookStepView:
    return PlaybookStepView(
        step_id=row.step_id,
        name=row.name,
        goal=row.goal,
        tool_selector=row.tool_selector,
        required=row.required,
        order_constraint=row.order_constraint,
        preconditions=list(row.preconditions),
        expected_evidence=row.expected_evidence,
        completion_check=row.completion_check,
        failure_action=row.failure_action,
    )


def to_hypothesis_view(row: HypothesisRow) -> HypothesisView:
    return HypothesisView(
        hypothesis_id=as_hypothesis_id(row.hypothesis_id),
        statement=row.statement,
        status=HypothesisStatus(row.status),
        confidence_score=row.confidence_score,
        last_updated_at=row.last_updated_at,
    )


def to_task_view(row: TaskRow) -> TaskView:
    return TaskView(
        task_id=row.task_id,
        linked_hypothesis_id=(
            as_hypothesis_id(row.linked_hypothesis_id)
            if row.linked_hypothesis_id is not None
            else None
        ),
        intent=row.intent,
        expected_evidence=row.expected_evidence,
        expected_information_gain=row.expected_information_gain,
        expected_value=row.expected_value,
        tool_name=row.tool_name,
        tool_input_objective=row.tool_input_objective,
        tool_input_step=row.tool_input_step,
        tool_input_reason=row.tool_input_reason,
        tool_input_evidence_id=row.tool_input_evidence_id,
        status=TaskStatus(row.status),
        priority=row.priority,
        created_reason=row.created_reason,
        updated_at=row.updated_at,
    )


def to_evidence_view(row: EvidenceRecordRow) -> EvidenceRecordView:
    return EvidenceRecordView(
        evidence_id=row.evidence_id,
        tool_execution_id=row.tool_execution_id,
        source=row.source,
        finding_summary=row.finding_summary,
        original_char_count=row.original_char_count,
        anomalies=list(row.anomalies),
        confidence_impact=row.confidence_impact,
        novelty_signal=row.novelty_signal,
        raw_output_size_bytes=row.raw_output_size_bytes,
        detail_reason=row.detail_reason,
    )


def to_mandatory_check_view(row: CaseMandatoryCheckRow) -> MandatoryCheckView:
    return MandatoryCheckView(
        check_id=row.check_id,
        description=row.description,
    )


def to_termination_snapshot_view(row: TerminationSnapshotRow) -> TerminationSnapshotView:
    return TerminationSnapshotView(
        loop_count=row.loop_count,
        objective_satisfied=row.objective_satisfied,
        evidence_completeness_sufficient=row.evidence_completeness_sufficient,
        confidence_sufficient=row.confidence_sufficient,
        timeout_reached=row.timeout_reached,
        no_novel_signal=row.no_novel_signal,
        expected_value_below_threshold=row.expected_value_below_threshold,
        escalation_required=row.escalation_required,
        should_stop=row.should_stop,
        reason=row.reason,
    )
