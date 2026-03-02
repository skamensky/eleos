from enum import Enum

from pydantic import BaseModel, Field

from eleos.models.enums import HypothesisStatus
from eleos.models.ids import HypothesisId


class SeededHypothesisDraft(BaseModel):
    hypothesis_id: HypothesisId
    statement: str
    status: HypothesisStatus = HypothesisStatus.OPEN
    confidence_score: float = Field(ge=0.0, le=1.0)


class HypothesisSeedOutput(BaseModel):
    hypotheses: list[SeededHypothesisDraft] = Field(default_factory=list)


class SeededTaskDraft(BaseModel):
    step_id: str
    linked_hypothesis_id: HypothesisId | None = None
    intent: str
    expected_evidence: str
    expected_information_gain: float = Field(ge=0.0, le=1.0)
    expected_value: float = Field(ge=0.0, le=1.0)


class TaskSeedOutput(BaseModel):
    tasks: list[SeededTaskDraft] = Field(default_factory=list)


class HypothesisAssessment(BaseModel):
    hypothesis_id: HypothesisId
    confidence_score: float = Field(ge=0.0, le=1.0)
    status: HypothesisStatus
    supports_evidence: bool = False
    contradicts_evidence: bool = False


class HypothesisUpdateOutput(BaseModel):
    assessments: list[HypothesisAssessment] = Field(default_factory=list)


class FollowupTaskOutput(BaseModel):
    should_create: bool
    linked_hypothesis_id: HypothesisId | None = None
    intent: str | None = None
    expected_evidence: str | None = None
    expected_information_gain: float | None = Field(default=None, ge=0.0, le=1.0)
    expected_value: float | None = Field(default=None, ge=0.0, le=1.0)
    tool_name: str | None = None


class ReplanTaskOutput(BaseModel):
    linked_hypothesis_id: HypothesisId | None = None
    intent: str
    expected_evidence: str
    expected_information_gain: float = Field(ge=0.0, le=1.0)
    expected_value: float = Field(ge=0.0, le=1.0)
    tool_name: str


class RawDetailDecision(BaseModel):
    needs_raw_detail: bool
    reason: str


class TaskSelectionOutcome(str, Enum):
    SELECTED = "selected"
    PRUNED = "pruned"
    NONE = "none"


class TaskSelectionDecision(BaseModel):
    selected_task_id: str | None = None
    prune_task_id: str | None = None
    outcome: TaskSelectionOutcome
    reason: str
