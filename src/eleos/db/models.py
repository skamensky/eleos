from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from eleos.settings.config import config

_db_metadata = MetaData(schema=config.persistence.db_schema)


class Base(DeclarativeBase):
    metadata = _db_metadata


class CaseRunRow(Base):
    __tablename__ = "case_runs"

    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    case_class: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    playbook_policy: Mapped[str] = mapped_column(String, nullable=False)
    timeout_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    completion_require_objective_satisfied: Mapped[bool] = mapped_column(Boolean, nullable=False)
    completion_require_evidence_completeness: Mapped[bool] = mapped_column(Boolean, nullable=False)
    completion_require_confidence_threshold: Mapped[bool] = mapped_column(Boolean, nullable=False)
    completion_allow_stop_on_timeout: Mapped[bool] = mapped_column(Boolean, nullable=False)

    request_source_channel: Mapped[str | None] = mapped_column(String)
    request_requester: Mapped[str | None] = mapped_column(String)
    request_tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    escalation_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    loop_count: Mapped[int] = mapped_column(Integer, nullable=False)
    last_novelty_signal: Mapped[float | None] = mapped_column(Float)
    critic_depth_multiplier: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CaseMandatoryCheckRow(Base):
    __tablename__ = "case_mandatory_checks"

    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        primary_key=True,
    )
    check_id: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    passed: Mapped[bool | None] = mapped_column(Boolean)
    reason: Mapped[str | None] = mapped_column(Text)


class HypothesisRow(Base):
    __tablename__ = "case_hypotheses"

    hypothesis_id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TaskRow(Base):
    __tablename__ = "case_tasks"

    task_id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    linked_hypothesis_id: Mapped[str | None] = mapped_column(String)
    intent: Mapped[str] = mapped_column(Text, nullable=False)
    expected_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    expected_information_gain: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    tool_input_objective: Mapped[str] = mapped_column(Text, nullable=False)
    tool_input_step: Mapped[str | None] = mapped_column(String)
    tool_input_reason: Mapped[str | None] = mapped_column(Text)
    tool_input_evidence_id: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    created_reason: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ToolExecutionRow(Base):
    __tablename__ = "tool_executions"

    tool_execution_id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    input_handle: Mapped[str] = mapped_column(String, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvidenceRecordRow(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint("case_id", "tool_execution_id", name="uq_evidence_case_tool_execution"),
    )

    evidence_id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_execution_id: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    finding_summary: Mapped[str] = mapped_column(Text, nullable=False)
    original_char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    anomalies: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    confidence_impact: Mapped[float] = mapped_column(Float, nullable=False)
    novelty_signal: Mapped[float] = mapped_column(Float, nullable=False)

    raw_output_hash: Mapped[str] = mapped_column(String, nullable=False)
    raw_output_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    detail_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class HypothesisEvidenceLinkRow(Base):
    __tablename__ = "hypothesis_evidence_links"

    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.case_hypotheses.hypothesis_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.evidence_records.evidence_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    relation: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TaskHypothesisLinkRow(Base):
    __tablename__ = "task_hypothesis_links"

    task_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_tasks.task_id", ondelete="CASCADE"),
        primary_key=True,
    )
    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.case_hypotheses.hypothesis_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )


class TaskEvidenceLinkRow(Base):
    __tablename__ = "task_evidence_links"

    task_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_tasks.task_id", ondelete="CASCADE"),
        primary_key=True,
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.evidence_records.evidence_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )


class ToolOutputRow(Base):
    __tablename__ = "tool_outputs"
    __table_args__ = (
        UniqueConstraint("case_id", "tool_execution_id", name="uq_tool_outputs_case_execution"),
    )

    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_execution_id: Mapped[str] = mapped_column(String, primary_key=True)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CognitionRecordRow(Base):
    __tablename__ = "cognition_records"

    record_id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    record_type: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    decision_action: Mapped[str | None] = mapped_column(String)
    decision_reason: Mapped[str | None] = mapped_column(Text)

    feedback_requires_replan: Mapped[bool | None] = mapped_column(Boolean)
    feedback_reason: Mapped[str | None] = mapped_column(Text)
    feedback_novelty_score: Mapped[float | None] = mapped_column(Float)
    feedback_drift_score: Mapped[float | None] = mapped_column(Float)

    insight_text: Mapped[str | None] = mapped_column(Text)


class CognitionHypothesisLinkRow(Base):
    __tablename__ = "cognition_hypothesis_links"

    record_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.cognition_records.record_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.case_hypotheses.hypothesis_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )


class CognitionEvidenceLinkRow(Base):
    __tablename__ = "cognition_evidence_links"

    record_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.cognition_records.record_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.evidence_records.evidence_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )


class TerminationSnapshotRow(Base):
    __tablename__ = "termination_snapshots"

    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        primary_key=True,
    )
    loop_count: Mapped[int] = mapped_column(Integer, primary_key=True)
    objective_satisfied: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evidence_completeness_sufficient: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence_sufficient: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timeout_reached: Mapped[bool] = mapped_column(Boolean, nullable=False)
    no_novel_signal: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expected_value_below_threshold: Mapped[bool] = mapped_column(Boolean, nullable=False)
    escalation_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    should_stop: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CaseFinalReportRow(Base):
    __tablename__ = "case_final_reports"
    __table_args__ = (
        ForeignKeyConstraint(
            ["case_id", "termination_loop_count"],
            [
                f"{config.persistence.db_schema}.termination_snapshots.case_id",
                f"{config.persistence.db_schema}.termination_snapshots.loop_count",
            ],
            ondelete="RESTRICT",
        ),
    )

    case_id: Mapped[str] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.case_runs.case_id", ondelete="CASCADE"),
        primary_key=True,
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    final_assessment: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_label: Mapped[str] = mapped_column(String, nullable=False)
    completion_gate_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    customer_followups: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    internal_support_followups: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    escalation: Mapped[str | None] = mapped_column(Text)

    termination_loop_count: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CaseFinalReportCheckRow(Base):
    __tablename__ = "case_final_report_checks"

    case_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.case_final_reports.case_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    check_id: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class CaseFinalReportEvidenceLinkRow(Base):
    __tablename__ = "case_final_report_evidence_links"

    case_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.case_final_reports.case_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.evidence_records.evidence_id",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )


class CaseFinalReportHypothesisLinkRow(Base):
    __tablename__ = "case_final_report_hypothesis_links"

    case_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.case_final_reports.case_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey(
            f"{config.persistence.db_schema}.case_hypotheses.hypothesis_id",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )


class PlaybookRow(Base):
    __tablename__ = "playbooks"
    __table_args__ = (UniqueConstraint("playbook_id", "version", name="uq_playbook_id_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playbook_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    enforcement_mode: Mapped[str] = mapped_column(String, nullable=False)
    applicable_case_classes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    objective_template: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    steps: Mapped[list["PlaybookStepRow"]] = relationship(
        back_populates="playbook",
        cascade="all, delete-orphan",
        order_by="PlaybookStepRow.step_order",
        lazy="raise",
    )


class PlaybookStepRow(Base):
    __tablename__ = "playbook_steps"
    __table_args__ = (UniqueConstraint("playbook_fk", "step_id", name="uq_playbook_step"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playbook_fk: Mapped[int] = mapped_column(
        ForeignKey(f"{config.persistence.db_schema}.playbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    tool_selector: Mapped[str] = mapped_column(String, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    order_constraint: Mapped[str] = mapped_column(String, nullable=False)
    preconditions: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    expected_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    completion_check: Mapped[str] = mapped_column(Text, nullable=False)
    failure_action: Mapped[str] = mapped_column(String, nullable=False)

    playbook: Mapped[PlaybookRow] = relationship(back_populates="steps", lazy="raise")
