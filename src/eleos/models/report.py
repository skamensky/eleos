from pydantic import BaseModel, ConfigDict, Field

from eleos.db.models import HypothesisRow, TerminationSnapshotRow


class CompletionCheckStatus(BaseModel):
    check_id: str
    description: str
    passed: bool
    reason: str


class CompletionGateStatus(BaseModel):
    passed: bool
    checks: list[CompletionCheckStatus] = Field(default_factory=list)


class FinalReport(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    objective: str
    final_assessment: str
    hypotheses_considered: list[HypothesisRow]
    evidence_ledger_refs: list[str]
    confidence_score: float
    confidence_label: str
    completion_gate_status: CompletionGateStatus
    citations: list[str]
    escalation: str | None
    customer_followups: list[str]
    internal_support_followups: list[str]
    termination_snapshot: TerminationSnapshotRow
