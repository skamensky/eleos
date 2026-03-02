from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from eleos.api.models import (
    CaseRunDetailResponse,
    CaseRunSummaryResponse,
    CaseRunTimelineResponse,
    CaseTimelineEventResponse,
    CaseTimelineEventType,
    CaseTimelineReferenceResponse,
    CategoryOptionResponse,
    CognitionRecordResponse,
    FinalReportStoredResponse,
    PlaybookCreateRequest,
    PlaybookFormOptionsResponse,
    ToolOptionResponse,
    to_case_run_summary_response,
    to_cognition_record_response,
    to_final_report_stored_response,
    to_hypothesis_evidence_link_response,
    to_mandatory_check_state_response,
    to_playbook_step_row,
    to_termination_snapshot_views,
    to_tool_execution_response,
    to_tool_output_response,
)
from eleos.core.tool_catalog import get_tool_catalog
from eleos.db.engine import session_scope
from eleos.db.models import (
    CaseFinalReportCheckRow,
    CaseFinalReportEvidenceLinkRow,
    CaseFinalReportHypothesisLinkRow,
    CaseFinalReportRow,
    CaseMandatoryCheckRow,
    CaseRunRow,
    CognitionEvidenceLinkRow,
    CognitionHypothesisLinkRow,
    CognitionRecordRow,
    EvidenceRecordRow,
    HypothesisEvidenceLinkRow,
    HypothesisRow,
    PlaybookRow,
    TaskEvidenceLinkRow,
    TaskHypothesisLinkRow,
    TaskRow,
    TerminationSnapshotRow,
    ToolExecutionRow,
    ToolOutputRow,
)
from eleos.db.views.mappers import (
    to_evidence_view,
    to_hypothesis_view,
    to_playbook_view,
    to_task_view,
)
from eleos.db.views.models import PlaybookView, TerminationSnapshotView
from eleos.models.enums import EnforcementMode, FailureAction, OrderConstraint, PlaybookStatus
from eleos.settings.config import config


def list_playbooks(*, limit: int) -> list[PlaybookView]:
    with session_scope() as session:
        rows = list(
            session.scalars(
                select(PlaybookRow)
                .options(selectinload(PlaybookRow.steps))
                .order_by(PlaybookRow.updated_at.desc())
                .limit(limit)
            ).all()
        )
    return [to_playbook_view(row) for row in rows]


def get_playbook_form_options() -> PlaybookFormOptionsResponse:
    catalog = get_tool_catalog()
    categories = [
        CategoryOptionResponse(
            category_id=category.category_id,
            description=category.description,
            required_tool_references=list(category.required_tool_references),
            suggested_tool_references=list(category.suggested_tool_references),
        )
        for category in config.classification.categories
    ]
    tools = [
        ToolOptionResponse(
            tool_name=entry.tool_name,
            function_description=entry.function_description,
        )
        for entry in catalog.by_tool_name.values()
    ]
    tools.sort(key=lambda entry: entry.tool_name)
    return PlaybookFormOptionsResponse(
        categories=categories,
        tools=tools,
        enforcement_modes=[item.value for item in EnforcementMode],
        order_constraints=[item.value for item in OrderConstraint],
        failure_actions=[item.value for item in FailureAction],
        statuses=[item.value for item in PlaybookStatus],
    )


def create_playbook(payload: PlaybookCreateRequest) -> PlaybookView:
    if not payload.steps:
        raise ValueError("playbook must include at least one step")
    step_ids = {step.step_id for step in payload.steps}
    if len(step_ids) != len(payload.steps):
        raise ValueError("duplicate step_id values in playbook steps")
    playbook_id = _resolve_playbook_id(payload)

    with session_scope() as session:
        existing = session.scalar(
            select(PlaybookRow.id).where(
                PlaybookRow.playbook_id == playbook_id,
                PlaybookRow.version == payload.version,
            )
        )
        if existing is not None:
            raise ValueError(
                f"playbook already exists for id={playbook_id} version={payload.version}"
            )
        row = PlaybookRow(
            playbook_id=playbook_id,
            version=payload.version,
            title=payload.title,
            status=payload.status,
            enforcement_mode=payload.enforcement_mode,
            applicable_case_classes=list(payload.applicable_case_classes),
            objective_template=payload.objective_template,
            created_by=payload.created_by,
        )
        session.add(row)
        session.flush()
        for step in payload.steps:
            session.add(to_playbook_step_row(step, playbook_fk=row.id))
        session.flush()
        hydrated = session.scalar(
            select(PlaybookRow)
            .options(selectinload(PlaybookRow.steps))
            .where(PlaybookRow.id == row.id)
        )
    if hydrated is None:
        raise RuntimeError("created playbook row missing")
    return to_playbook_view(hydrated)


def _resolve_playbook_id(payload: PlaybookCreateRequest) -> str:
    if payload.playbook_id is not None and payload.playbook_id.strip():
        return payload.playbook_id.strip()
    base = re.sub(r"[^a-z0-9]+", "_", payload.title.lower()).strip("_")
    if not base:
        base = "playbook"
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{base}_{timestamp}"


def list_case_runs(*, limit: int) -> list[CaseRunSummaryResponse]:
    with session_scope() as session:
        rows = list(
            session.scalars(
                select(CaseRunRow).order_by(CaseRunRow.created_at.desc()).limit(limit)
            ).all()
        )
    return [to_case_run_summary_response(row) for row in rows]


def get_case_run_detail(case_id: str) -> CaseRunDetailResponse | None:
    with session_scope() as session:
        case_row = session.get(CaseRunRow, case_id)
        if case_row is None:
            return None

        mandatory_checks = list(
            session.scalars(
                select(CaseMandatoryCheckRow)
                .where(CaseMandatoryCheckRow.case_id == case_id)
                .order_by(CaseMandatoryCheckRow.check_id.asc())
            ).all()
        )
        hypotheses = list(
            session.scalars(
                select(HypothesisRow)
                .where(HypothesisRow.case_id == case_id)
                .order_by(HypothesisRow.last_updated_at.asc())
            ).all()
        )
        tasks = list(
            session.scalars(
                select(TaskRow)
                .where(TaskRow.case_id == case_id)
                .order_by(TaskRow.priority.asc(), TaskRow.updated_at.asc())
            ).all()
        )
        task_ids = [row.task_id for row in tasks]
        task_h_links = list(
            session.scalars(
                select(TaskHypothesisLinkRow).where(TaskHypothesisLinkRow.task_id.in_(task_ids))
            ).all()
        ) if task_ids else []
        task_e_links = list(
            session.scalars(
                select(TaskEvidenceLinkRow).where(TaskEvidenceLinkRow.task_id.in_(task_ids))
            ).all()
        ) if task_ids else []

        tool_executions = list(
            session.scalars(
                select(ToolExecutionRow)
                .where(ToolExecutionRow.case_id == case_id)
                .order_by(ToolExecutionRow.started_at.asc())
            ).all()
        )
        tool_outputs = list(
            session.scalars(
                select(ToolOutputRow)
                .where(ToolOutputRow.case_id == case_id)
                .order_by(ToolOutputRow.created_at.asc())
            ).all()
        )
        evidence_records = list(
            session.scalars(
                select(EvidenceRecordRow)
                .where(EvidenceRecordRow.case_id == case_id)
                .order_by(EvidenceRecordRow.created_at.asc())
            ).all()
        )
        hypothesis_evidence_links = list(
            session.scalars(
                select(HypothesisEvidenceLinkRow)
                .join(
                    HypothesisRow,
                    HypothesisRow.hypothesis_id == HypothesisEvidenceLinkRow.hypothesis_id,
                )
                .where(HypothesisRow.case_id == case_id)
                .order_by(HypothesisEvidenceLinkRow.created_at.asc())
            ).all()
        )

        cognition_records = list(
            session.scalars(
                select(CognitionRecordRow)
                .where(CognitionRecordRow.case_id == case_id)
                .order_by(CognitionRecordRow.timestamp.asc())
            ).all()
        )
        cognition_ids = [row.record_id for row in cognition_records]
        cognition_h_links = list(
            session.scalars(
                select(CognitionHypothesisLinkRow).where(
                    CognitionHypothesisLinkRow.record_id.in_(cognition_ids)
                )
            ).all()
        ) if cognition_ids else []
        cognition_e_links = list(
            session.scalars(
                select(CognitionEvidenceLinkRow).where(
                    CognitionEvidenceLinkRow.record_id.in_(cognition_ids)
                )
            ).all()
        ) if cognition_ids else []

        termination_snapshots = list(
            session.scalars(
                select(TerminationSnapshotRow)
                .where(TerminationSnapshotRow.case_id == case_id)
                .order_by(TerminationSnapshotRow.loop_count.asc())
            ).all()
        )
        final_report = session.get(CaseFinalReportRow, case_id)
        final_report_checks = list(
            session.scalars(
                select(CaseFinalReportCheckRow)
                .where(CaseFinalReportCheckRow.case_id == case_id)
                .order_by(CaseFinalReportCheckRow.check_id.asc())
            ).all()
        )
        final_report_evidence = list(
            session.scalars(
                select(CaseFinalReportEvidenceLinkRow).where(
                    CaseFinalReportEvidenceLinkRow.case_id == case_id
                )
            ).all()
        )
        final_report_hypotheses = list(
            session.scalars(
                select(CaseFinalReportHypothesisLinkRow).where(
                    CaseFinalReportHypothesisLinkRow.case_id == case_id
                )
            ).all()
        )

    task_hypothesis_links: dict[str, list[str]] = defaultdict(list)
    for link in task_h_links:
        task_hypothesis_links[link.task_id].append(link.hypothesis_id)

    task_evidence_links: dict[str, list[str]] = defaultdict(list)
    for link in task_e_links:
        task_evidence_links[link.task_id].append(link.evidence_id)

    cognition_hypothesis_links: dict[str, list[str]] = defaultdict(list)
    for link in cognition_h_links:
        cognition_hypothesis_links[link.record_id].append(link.hypothesis_id)

    cognition_evidence_links: dict[str, list[str]] = defaultdict(list)
    for link in cognition_e_links:
        cognition_evidence_links[link.record_id].append(link.evidence_id)

    persisted_final_report: FinalReportStoredResponse | None = None
    if final_report is not None:
        persisted_final_report = to_final_report_stored_response(
            final_report,
            checks=final_report_checks,
            evidence_links=final_report_evidence,
            hypothesis_links=final_report_hypotheses,
        )

    return CaseRunDetailResponse(
        summary=to_case_run_summary_response(case_row),
        mandatory_checks=[to_mandatory_check_state_response(row) for row in mandatory_checks],
        hypotheses=[to_hypothesis_view(row) for row in hypotheses],
        tasks=[to_task_view(row) for row in tasks],
        task_hypothesis_links={key: list(values) for key, values in task_hypothesis_links.items()},
        task_evidence_links={key: list(values) for key, values in task_evidence_links.items()},
        tool_executions=[to_tool_execution_response(row) for row in tool_executions],
        tool_outputs=[to_tool_output_response(row) for row in tool_outputs],
        evidence_records=[to_evidence_view(row) for row in evidence_records],
        hypothesis_evidence_links=[
            to_hypothesis_evidence_link_response(row)
            for row in hypothesis_evidence_links
        ],
        cognition_records=[
            to_cognition_record_response(
                row,
                linked_hypothesis_ids=cognition_hypothesis_links.get(row.record_id, []),
                linked_evidence_ids=cognition_evidence_links.get(row.record_id, []),
            )
            for row in cognition_records
        ],
        termination_snapshots=to_termination_snapshot_views(termination_snapshots),
        final_report=persisted_final_report,
    )


def get_case_run_timeline(case_id: str) -> CaseRunTimelineResponse | None:
    detail = get_case_run_detail(case_id)
    if detail is None:
        return None

    with session_scope() as session:
        evidence_timestamps = {
            evidence_id: created_at
            for evidence_id, created_at in session.execute(
                select(EvidenceRecordRow.evidence_id, EvidenceRecordRow.created_at).where(
                    EvidenceRecordRow.case_id == case_id
                )
            ).all()
        }
        termination_timestamps = {
            loop_count: created_at
            for loop_count, created_at in session.execute(
                select(TerminationSnapshotRow.loop_count, TerminationSnapshotRow.created_at).where(
                    TerminationSnapshotRow.case_id == case_id
                )
            ).all()
        }

    hypothesis_by_id = {
        str(hypothesis.hypothesis_id): hypothesis.statement for hypothesis in detail.hypotheses
    }
    evidence_by_id = {
        evidence.evidence_id: evidence.finding_summary for evidence in detail.evidence_records
    }

    latest_termination = (
        detail.termination_snapshots[-1] if detail.termination_snapshots else None
    )
    unresolved_blockers = _build_unresolved_blockers(detail, latest_termination)

    tool_start_event_id: dict[str, str] = {}
    events: list[CaseTimelineEventResponse] = [
        CaseTimelineEventResponse(
            event_id=f"case_started:{detail.summary.case_id}",
            event_type=CaseTimelineEventType.CASE_STARTED,
            occurred_at=detail.summary.created_at,
            title="Case Started",
            summary=f"Investigation opened for objective: {detail.summary.objective}",
            detail=(
                f"Class: {detail.summary.case_class}. Mode: {detail.summary.mode}. "
                f"Playbook policy: {detail.summary.playbook_policy}."
            ),
        )
    ]

    for task in detail.tasks:
        linked_hypothesis_ids = detail.task_hypothesis_links.get(task.task_id, [])
        references: list[CaseTimelineReferenceResponse] = [
            CaseTimelineReferenceResponse(
                reference_type="task",
                reference_id=task.task_id,
                label=task.intent,
            )
        ]
        for hypothesis_id in linked_hypothesis_ids:
            references.append(
                CaseTimelineReferenceResponse(
                    reference_type="hypothesis",
                    reference_id=hypothesis_id,
                    label=hypothesis_by_id.get(hypothesis_id),
                )
            )

        events.append(
            CaseTimelineEventResponse(
                event_id=f"task:{task.task_id}",
                event_type=CaseTimelineEventType.TASK_UPSERTED,
                occurred_at=task.updated_at,
                title="Task Updated",
                summary=(
                    f"{task.intent} (tool: {task.tool_name}, status: {task.status.value})"
                ),
                detail=(
                    f"Expected evidence: {task.expected_evidence}. "
                    f"Created reason: {task.created_reason}."
                ),
                references=references,
            )
        )

    for execution in detail.tool_executions:
        start_event_id = f"tool_started:{execution.tool_execution_id}"
        tool_start_event_id[execution.tool_execution_id] = start_event_id
        events.append(
            CaseTimelineEventResponse(
                event_id=start_event_id,
                event_type=CaseTimelineEventType.TOOL_EXECUTION,
                occurred_at=execution.started_at,
                title="Tool Execution Started",
                summary=f"{execution.tool_name} execution started ({execution.status}).",
                detail=f"Input handle: {execution.input_handle}.",
                references=[
                    CaseTimelineReferenceResponse(
                        reference_type="tool_execution",
                        reference_id=execution.tool_execution_id,
                        label=execution.tool_name,
                    )
                ],
            )
        )
        if execution.finished_at is not None:
            finish_summary = f"{execution.tool_name} execution finished ({execution.status})."
            if execution.error:
                finish_summary = (
                    f"{execution.tool_name} execution finished with error ({execution.status})."
                )
            finish_detail = (
                f"Duration: {execution.duration_ms}ms."
                if execution.duration_ms is not None
                else "Duration unavailable."
            )
            if execution.error:
                finish_detail = f"{finish_detail} Error: {execution.error}"
            events.append(
                CaseTimelineEventResponse(
                    event_id=f"tool_finished:{execution.tool_execution_id}",
                    event_type=CaseTimelineEventType.TOOL_EXECUTION,
                    occurred_at=execution.finished_at,
                    title="Tool Execution Finished",
                    summary=finish_summary,
                    detail=finish_detail,
                    caused_by_event_id=start_event_id,
                    references=[
                        CaseTimelineReferenceResponse(
                            reference_type="tool_execution",
                            reference_id=execution.tool_execution_id,
                            label=execution.tool_name,
                        )
                    ],
                )
            )

    for evidence in detail.evidence_records:
        tool_event_id = tool_start_event_id.get(evidence.tool_execution_id)
        events.append(
            CaseTimelineEventResponse(
                event_id=f"evidence:{evidence.evidence_id}",
                event_type=CaseTimelineEventType.EVIDENCE_RECORDED,
                occurred_at=evidence_timestamps.get(
                    evidence.evidence_id, detail.summary.updated_at
                ),
                title="Evidence Recorded",
                summary=evidence.finding_summary,
                detail=(
                    f"Source: {evidence.source}. Novelty: {evidence.novelty_signal}. "
                    f"Confidence impact: {evidence.confidence_impact}. "
                    f"Original chars: {evidence.original_char_count}."
                ),
                caused_by_event_id=tool_event_id,
                references=[
                    CaseTimelineReferenceResponse(
                        reference_type="evidence",
                        reference_id=evidence.evidence_id,
                        label=evidence.source,
                    ),
                    CaseTimelineReferenceResponse(
                        reference_type="tool_execution",
                        reference_id=evidence.tool_execution_id,
                    ),
                ],
            )
        )

    for cognition in detail.cognition_records:
        linked_evidence_ids = list(cognition.linked_evidence_ids)
        linked_hypothesis_ids = list(cognition.linked_hypothesis_ids)
        summary = _cognition_summary(cognition)
        detail_lines: list[str] = []
        if linked_hypothesis_ids:
            hypothesis_labels = [
                hypothesis_by_id.get(hypothesis_id, hypothesis_id)
                for hypothesis_id in linked_hypothesis_ids
            ]
            detail_lines.append(
                f"Hypotheses considered: {', '.join(hypothesis_labels)}."
            )
        if linked_evidence_ids:
            evidence_labels = [
                evidence_by_id.get(evidence_id, evidence_id) for evidence_id in linked_evidence_ids
            ]
            detail_lines.append(
                f"Evidence used: {' | '.join(evidence_labels[:3])}."
            )

        references = [
            CaseTimelineReferenceResponse(
                reference_type="cognition_record",
                reference_id=cognition.record_id,
                label=cognition.record_type,
            )
        ]
        for hypothesis_id in linked_hypothesis_ids:
            references.append(
                CaseTimelineReferenceResponse(
                    reference_type="hypothesis",
                    reference_id=hypothesis_id,
                    label=hypothesis_by_id.get(hypothesis_id),
                )
            )
        for evidence_id in linked_evidence_ids:
            references.append(
                CaseTimelineReferenceResponse(
                    reference_type="evidence",
                    reference_id=evidence_id,
                    label=evidence_by_id.get(evidence_id),
                )
            )

        caused_by_event_id = (
            f"evidence:{linked_evidence_ids[0]}" if linked_evidence_ids else None
        )
        events.append(
            CaseTimelineEventResponse(
                event_id=f"cognition:{cognition.record_id}",
                event_type=CaseTimelineEventType.COGNITION_RECORDED,
                occurred_at=cognition.timestamp,
                title=f"Cognition: {_cognition_title(cognition.record_type)}",
                summary=summary,
                detail="\n".join(detail_lines) if detail_lines else None,
                caused_by_event_id=caused_by_event_id,
                references=references,
            )
        )

    for snapshot in detail.termination_snapshots:
        refs = [
            CaseTimelineReferenceResponse(
                reference_type="termination_loop",
                reference_id=str(snapshot.loop_count),
                label=f"Loop {snapshot.loop_count}",
            )
        ]
        events.append(
            CaseTimelineEventResponse(
                event_id=f"termination:{snapshot.loop_count}",
                event_type=CaseTimelineEventType.TERMINATION_EVALUATED,
                occurred_at=termination_timestamps.get(
                    snapshot.loop_count, detail.summary.updated_at
                ),
                title=f"Termination Evaluation (Loop {snapshot.loop_count})",
                summary=snapshot.reason,
                detail=(
                    f"objective_satisfied={snapshot.objective_satisfied}, "
                    f"evidence_completeness={snapshot.evidence_completeness_sufficient}, "
                    f"confidence={snapshot.confidence_sufficient}, "
                    f"timeout_reached={snapshot.timeout_reached}, "
                    f"no_novel_signal={snapshot.no_novel_signal}, "
                    f"expected_value_below_threshold={snapshot.expected_value_below_threshold}."
                ),
                references=refs,
            )
        )

    if detail.final_report is not None:
        check_refs = [
            CaseTimelineReferenceResponse(
                reference_type="final_report_check",
                reference_id=check.check_id,
                label=f"{check.description} => {check.passed}",
            )
            for check in detail.final_report.checks
        ]
        events.append(
            CaseTimelineEventResponse(
                event_id=f"final_report:{detail.summary.case_id}",
                event_type=CaseTimelineEventType.FINAL_REPORT_STORED,
                occurred_at=detail.final_report.created_at,
                title="Final Report Stored",
                summary=detail.final_report.final_assessment,
                detail=(
                    f"Confidence: {detail.final_report.confidence_label} "
                    f"({detail.final_report.confidence_score}). "
                    f"Completion gate passed: {detail.final_report.completion_gate_passed}."
                ),
                caused_by_event_id=f"termination:{detail.final_report.termination_loop_count}",
                references=check_refs,
            )
        )

    sorted_events = sorted(
        events,
        key=lambda event: (event.occurred_at, event.event_id),
    )
    return CaseRunTimelineResponse(
        case_id=detail.summary.case_id,
        objective=detail.summary.objective,
        status=detail.summary.status,
        latest_stop_reason=latest_termination.reason if latest_termination else None,
        objective_satisfied=(
            latest_termination.objective_satisfied if latest_termination else None
        ),
        unresolved_blockers=unresolved_blockers,
        events=sorted_events,
    )


def _cognition_title(record_type: str) -> str:
    if record_type == "observation_record":
        return "Observation"
    if record_type == "decision_record":
        return "Decision"
    if record_type == "feedback_record":
        return "Feedback"
    if record_type == "insight_record":
        return "Insight"
    return record_type


def _cognition_summary(record: CognitionRecordResponse) -> str:
    if record.record_type == "decision_record":
        action = record.decision_action
        reason = record.decision_reason
        if action and reason:
            return f"Action: {action}. Reason: {reason}"
        if action:
            return f"Action: {action}."
        if reason:
            return f"Decision reason: {reason}"
        return "Decision recorded."
    if record.record_type == "feedback_record":
        requires_replan = record.feedback_requires_replan
        novelty = record.feedback_novelty_score
        drift = record.feedback_drift_score
        reason = record.feedback_reason
        return (
            f"Replan required: {requires_replan}. Novelty score: {novelty}. "
            f"Drift score: {drift}. Reason: {reason or 'n/a'}"
        )
    if record.record_type == "insight_record":
        return record.insight_text or "Insight recorded."
    return "Observation recorded."


def _build_unresolved_blockers(
    detail: CaseRunDetailResponse,
    latest_termination: TerminationSnapshotView | None,
) -> list[str]:
    blockers: list[str] = []
    final_report = detail.final_report
    if final_report is not None:
        for check in final_report.checks:
            if not check.passed:
                blockers.append(f"{check.description}: {check.reason}")

    if latest_termination is not None:
        if not latest_termination.objective_satisfied:
            blockers.append("Objective not satisfied by current evidence.")
        if not latest_termination.evidence_completeness_sufficient:
            blockers.append("Evidence completeness threshold not met.")
        if not latest_termination.confidence_sufficient:
            blockers.append("Confidence threshold not met.")
        if latest_termination.timeout_reached:
            blockers.append("Timeout reached before closure.")
        if latest_termination.no_novel_signal:
            blockers.append("No novel signal detected in recent loop(s).")
        if latest_termination.expected_value_below_threshold:
            blockers.append("Expected value dropped below threshold.")
    return list(dict.fromkeys(blockers))
