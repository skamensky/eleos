"""Initial schema for DB-first typed runtime persistence.

Revision ID: 20260228_0001
Revises: None
Create Date: 2026-02-28 10:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from eleos.settings.config import config as app_config

# revision identifiers, used by Alembic.
revision = "20260228_0001"
down_revision = None
branch_labels = None
depends_on = None


SCHEMA = app_config.persistence.db_schema


def upgrade() -> None:
    op.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))

    op.create_table(
        "case_runs",
        sa.Column("case_id", sa.String(), primary_key=True),
        sa.Column("case_class", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("playbook_policy", sa.String(), nullable=False),
        sa.Column("timeout_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completion_require_objective_satisfied", sa.Boolean(), nullable=False),
        sa.Column("completion_require_evidence_completeness", sa.Boolean(), nullable=False),
        sa.Column("completion_require_confidence_threshold", sa.Boolean(), nullable=False),
        sa.Column("completion_allow_stop_on_timeout", sa.Boolean(), nullable=False),
        sa.Column("request_source_channel", sa.String(), nullable=True),
        sa.Column("request_requester", sa.String(), nullable=True),
        sa.Column("request_tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("escalation_required", sa.Boolean(), nullable=False),
        sa.Column("loop_count", sa.Integer(), nullable=False),
        sa.Column("last_novelty_signal", sa.Float(), nullable=True),
        sa.Column("critic_depth_multiplier", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "case_mandatory_checks",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("check_id", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("case_id", "check_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "case_hypotheses",
        sa.Column("hypothesis_id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_case_hypotheses_case_id",
        "case_hypotheses",
        ["case_id"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index(
        "ix_case_hypotheses_status",
        "case_hypotheses",
        ["status"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_table(
        "case_tasks",
        sa.Column("task_id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("linked_hypothesis_id", sa.String(), nullable=True),
        sa.Column("intent", sa.Text(), nullable=False),
        sa.Column("expected_evidence", sa.Text(), nullable=False),
        sa.Column("expected_information_gain", sa.Float(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("tool_input_objective", sa.Text(), nullable=False),
        sa.Column("tool_input_step", sa.String(), nullable=True),
        sa.Column("tool_input_reason", sa.Text(), nullable=True),
        sa.Column("tool_input_evidence_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_reason", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        schema=SCHEMA,
    )
    op.create_index("ix_case_tasks_case_id", "case_tasks", ["case_id"], unique=False, schema=SCHEMA)
    op.create_index("ix_case_tasks_status", "case_tasks", ["status"], unique=False, schema=SCHEMA)

    op.create_table(
        "tool_executions",
        sa.Column("tool_execution_id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("input_handle", sa.String(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_tool_executions_case_id",
        "tool_executions",
        ["case_id"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index(
        "ix_tool_executions_status",
        "tool_executions",
        ["status"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_table(
        "evidence_records",
        sa.Column("evidence_id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("tool_execution_id", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("finding_summary", sa.Text(), nullable=False),
        sa.Column("original_char_count", sa.Integer(), nullable=False),
        sa.Column("anomalies", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("confidence_impact", sa.Float(), nullable=False),
        sa.Column("novelty_signal", sa.Float(), nullable=False),
        sa.Column("raw_output_hash", sa.String(), nullable=False),
        sa.Column("raw_output_size_bytes", sa.Integer(), nullable=False),
        sa.Column("detail_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("case_id", "tool_execution_id", name="uq_evidence_case_tool_execution"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_evidence_records_case_id",
        "evidence_records",
        ["case_id"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_table(
        "hypothesis_evidence_links",
        sa.Column("hypothesis_id", sa.String(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=False),
        sa.Column("relation", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hypothesis_id"],
            [f"{SCHEMA}.case_hypotheses.hypothesis_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            [f"{SCHEMA}.evidence_records.evidence_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("hypothesis_id", "evidence_id", "relation"),
        schema=SCHEMA,
    )

    op.create_table(
        "task_hypothesis_links",
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("hypothesis_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], [f"{SCHEMA}.case_tasks.task_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["hypothesis_id"],
            [f"{SCHEMA}.case_hypotheses.hypothesis_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", "hypothesis_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "task_evidence_links",
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], [f"{SCHEMA}.case_tasks.task_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            [f"{SCHEMA}.evidence_records.evidence_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", "evidence_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "tool_outputs",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("tool_execution_id", sa.String(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("tool_execution_id"),
        sa.UniqueConstraint("case_id", "tool_execution_id", name="uq_tool_outputs_case_execution"),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_tool_outputs_case_id",
        "tool_outputs",
        ["case_id"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_table(
        "cognition_records",
        sa.Column("record_id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("record_type", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decision_action", sa.String(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("feedback_requires_replan", sa.Boolean(), nullable=True),
        sa.Column("feedback_reason", sa.Text(), nullable=True),
        sa.Column("feedback_novelty_score", sa.Float(), nullable=True),
        sa.Column("feedback_drift_score", sa.Float(), nullable=True),
        sa.Column("insight_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_cognition_records_case_id",
        "cognition_records",
        ["case_id"],
        unique=False,
        schema=SCHEMA,
    )

    op.create_table(
        "cognition_hypothesis_links",
        sa.Column("record_id", sa.String(), nullable=False),
        sa.Column("hypothesis_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["record_id"],
            [f"{SCHEMA}.cognition_records.record_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hypothesis_id"],
            [f"{SCHEMA}.case_hypotheses.hypothesis_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("record_id", "hypothesis_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "cognition_evidence_links",
        sa.Column("record_id", sa.String(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["record_id"],
            [f"{SCHEMA}.cognition_records.record_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            [f"{SCHEMA}.evidence_records.evidence_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("record_id", "evidence_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "termination_snapshots",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("loop_count", sa.Integer(), nullable=False),
        sa.Column("objective_satisfied", sa.Boolean(), nullable=False),
        sa.Column("evidence_completeness_sufficient", sa.Boolean(), nullable=False),
        sa.Column("confidence_sufficient", sa.Boolean(), nullable=False),
        sa.Column("timeout_reached", sa.Boolean(), nullable=False),
        sa.Column("no_novel_signal", sa.Boolean(), nullable=False),
        sa.Column("expected_value_below_threshold", sa.Boolean(), nullable=False),
        sa.Column("escalation_required", sa.Boolean(), nullable=False),
        sa.Column("should_stop", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("case_id", "loop_count"),
        schema=SCHEMA,
    )

    op.create_table(
        "case_final_reports",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("final_assessment", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("confidence_label", sa.String(), nullable=False),
        sa.Column("completion_gate_passed", sa.Boolean(), nullable=False),
        sa.Column("customer_followups", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("internal_support_followups", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("escalation", sa.Text(), nullable=True),
        sa.Column("termination_loop_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], [f"{SCHEMA}.case_runs.case_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["case_id", "termination_loop_count"],
            [
                f"{SCHEMA}.termination_snapshots.case_id",
                f"{SCHEMA}.termination_snapshots.loop_count",
            ],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("case_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "case_final_report_checks",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("check_id", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            [f"{SCHEMA}.case_final_reports.case_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("case_id", "check_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "case_final_report_evidence_links",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            [f"{SCHEMA}.case_final_reports.case_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            [f"{SCHEMA}.evidence_records.evidence_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("case_id", "evidence_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "case_final_report_hypothesis_links",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("hypothesis_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"],
            [f"{SCHEMA}.case_final_reports.case_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hypothesis_id"],
            [f"{SCHEMA}.case_hypotheses.hypothesis_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("case_id", "hypothesis_id"),
        schema=SCHEMA,
    )

    op.create_table(
        "playbooks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("playbook_id", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("enforcement_mode", sa.String(), nullable=False),
        sa.Column("applicable_case_classes", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("objective_template", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("playbook_id", "version", name="uq_playbook_id_version"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_playbooks_playbook_id",
        "playbooks",
        ["playbook_id"],
        unique=False,
        schema=SCHEMA,
    )
    op.create_index("ix_playbooks_status", "playbooks", ["status"], unique=False, schema=SCHEMA)

    op.create_table(
        "playbook_steps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("playbook_fk", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("tool_selector", sa.String(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("order_constraint", sa.String(), nullable=False),
        sa.Column("preconditions", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("expected_evidence", sa.Text(), nullable=False),
        sa.Column("completion_check", sa.Text(), nullable=False),
        sa.Column("failure_action", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["playbook_fk"], [f"{SCHEMA}.playbooks.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("playbook_fk", "step_id", name="uq_playbook_step"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_playbook_steps_playbook_fk",
        "playbook_steps",
        ["playbook_fk"],
        unique=False,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_playbook_steps_playbook_fk", table_name="playbook_steps", schema=SCHEMA)
    op.drop_table("playbook_steps", schema=SCHEMA)

    op.drop_index("ix_playbooks_status", table_name="playbooks", schema=SCHEMA)
    op.drop_index("ix_playbooks_playbook_id", table_name="playbooks", schema=SCHEMA)
    op.drop_table("playbooks", schema=SCHEMA)

    op.drop_table("case_final_report_hypothesis_links", schema=SCHEMA)
    op.drop_table("case_final_report_evidence_links", schema=SCHEMA)
    op.drop_table("case_final_report_checks", schema=SCHEMA)
    op.drop_table("case_final_reports", schema=SCHEMA)

    op.drop_table("termination_snapshots", schema=SCHEMA)

    op.drop_table("cognition_evidence_links", schema=SCHEMA)
    op.drop_table("cognition_hypothesis_links", schema=SCHEMA)
    op.drop_index("ix_cognition_records_case_id", table_name="cognition_records", schema=SCHEMA)
    op.drop_table("cognition_records", schema=SCHEMA)

    op.drop_index("ix_tool_outputs_case_id", table_name="tool_outputs", schema=SCHEMA)
    op.drop_table("tool_outputs", schema=SCHEMA)

    op.drop_table("task_evidence_links", schema=SCHEMA)
    op.drop_table("task_hypothesis_links", schema=SCHEMA)
    op.drop_table("hypothesis_evidence_links", schema=SCHEMA)

    op.drop_index("ix_evidence_records_case_id", table_name="evidence_records", schema=SCHEMA)
    op.drop_table("evidence_records", schema=SCHEMA)

    op.drop_index("ix_tool_executions_status", table_name="tool_executions", schema=SCHEMA)
    op.drop_index("ix_tool_executions_case_id", table_name="tool_executions", schema=SCHEMA)
    op.drop_table("tool_executions", schema=SCHEMA)

    op.drop_index("ix_case_tasks_status", table_name="case_tasks", schema=SCHEMA)
    op.drop_index("ix_case_tasks_case_id", table_name="case_tasks", schema=SCHEMA)
    op.drop_table("case_tasks", schema=SCHEMA)

    op.drop_index("ix_case_hypotheses_status", table_name="case_hypotheses", schema=SCHEMA)
    op.drop_index("ix_case_hypotheses_case_id", table_name="case_hypotheses", schema=SCHEMA)
    op.drop_table("case_hypotheses", schema=SCHEMA)

    op.drop_table("case_mandatory_checks", schema=SCHEMA)

    op.drop_table("case_runs", schema=SCHEMA)
