from enum import Enum


class Mode(str, Enum):
    DEEP_INVESTIGATION = "deep_investigation"
    FAST_MODE = "fast_mode"


class PlaybookPolicy(str, Enum):
    MANDATORY = "mandatory"
    SUGGESTIVE = "suggestive"


class HypothesisStatus(str, Enum):
    OPEN = "open"
    SUPPORTED = "supported"
    REJECTED = "rejected"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    PRUNED = "pruned"
    FAILED = "failed"


class ToolExecutionStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PlaybookStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class EnforcementMode(str, Enum):
    SUGGESTIVE = "suggestive"
    MANDATORY = "mandatory"


class OrderConstraint(str, Enum):
    SEQUENTIAL = "sequential"
    CAN_SKIP_IF_CONDITION = "can_skip_if_condition"
    CONDITIONAL_BRANCH = "conditional_branch"


class FailureAction(str, Enum):
    RETRY = "retry"
    BRANCH = "branch"
    ESCALATE = "escalate"


class TerminationReason(str, Enum):
    CONTINUE = "continue"
    TIMEOUT_REACHED = "timeout_reached"
    ESCALATION_REQUIRED = "escalation_required"
    COMPLETION_CONDITIONS_MET = "completion_conditions_met"
    EXPLORATION_EXHAUSTED = "exploration_exhausted"


class CaseStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    ESCALATED = "escalated"
    EXHAUSTED = "exhausted"
    STOPPED = "stopped"


class CognitionRecordType(str, Enum):
    OBSERVATION = "observation_record"
    DECISION = "decision_record"
    FEEDBACK = "feedback_record"
    INSIGHT = "insight_record"


class DecisionAction(str, Enum):
    REPLAN = "replan"
    PRUNE_TASK = "prune_task"
    TOOL_FAILURE = "tool_failure"
    HYPOTHESIS_UPDATE = "hypothesis_update"


class LogEvent(str, Enum):
    INVESTIGATION_INITIALIZED = "investigation_initialized"
    TERMINATION_SNAPSHOT = "termination_snapshot"
    EVIDENCE_DETAIL_LOGGED = "evidence_detail_logged"
    AUDIT_PERSISTENCE_INITIALIZED = "audit_persistence_initialized"
