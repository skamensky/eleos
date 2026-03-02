from eleos.db.views.models import (
    FollowupTaskInputView,
    HypothesisSeedInputView,
    HypothesisUpdateInputView,
    RawDetailInputView,
    ReplanTaskInputView,
    TaskSeedInputView,
    TaskSelectionInputView,
)
from eleos.llm.agents.base.enums import SystemPrompt
from eleos.llm.agents.base.structured_agent import StructuredAgent, make_agent
from eleos.models.agents.planner.models import (
    FollowupTaskOutput,
    HypothesisSeedOutput,
    HypothesisUpdateOutput,
    RawDetailDecision,
    ReplanTaskOutput,
    TaskSeedOutput,
    TaskSelectionDecision,
)
from eleos.settings.config import config

hypothesis_seed_agent: StructuredAgent[HypothesisSeedInputView, HypothesisSeedOutput] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.PLANNER_HYPOTHESIS_SEED,
    input_model=HypothesisSeedInputView,
    output_model=HypothesisSeedOutput,
    output_name="hypothesis_seed",
    output_description="Initial hypothesis set for an investigation case",
)

task_seed_agent: StructuredAgent[TaskSeedInputView, TaskSeedOutput] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.PLANNER_TASK_SEED,
    input_model=TaskSeedInputView,
    output_model=TaskSeedOutput,
    output_name="task_seed",
    output_description="Initial task drafts aligned with playbook steps",
)

hypothesis_update_agent: StructuredAgent[
    HypothesisUpdateInputView,
    HypothesisUpdateOutput,
] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.PLANNER_HYPOTHESIS_UPDATE,
    input_model=HypothesisUpdateInputView,
    output_model=HypothesisUpdateOutput,
    output_name="hypothesis_update",
    output_description="Updated confidence and support/contradiction flags per hypothesis",
)

followup_task_agent: StructuredAgent[FollowupTaskInputView, FollowupTaskOutput] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.PLANNER_FOLLOWUP_TASK,
    input_model=FollowupTaskInputView,
    output_model=FollowupTaskOutput,
    output_name="followup_task",
    output_description="Decision for whether and how to add a follow-up task",
)

replan_task_agent: StructuredAgent[ReplanTaskInputView, ReplanTaskOutput] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.PLANNER_REPLAN_TASK,
    input_model=ReplanTaskInputView,
    output_model=ReplanTaskOutput,
    output_name="replan_task",
    output_description="Single replanned task to continue investigation progress",
)

raw_detail_agent: StructuredAgent[RawDetailInputView, RawDetailDecision] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.PLANNER_RAW_DETAIL,
    input_model=RawDetailInputView,
    output_model=RawDetailDecision,
    output_name="raw_detail_decision",
    output_description="Decision for whether full raw tool payload should be fetched",
)

task_selection_agent: StructuredAgent[TaskSelectionInputView, TaskSelectionDecision] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.PLANNER_TASK_SELECTION,
    input_model=TaskSelectionInputView,
    output_model=TaskSelectionDecision,
    output_name="task_selection",
    output_description="Decision for selecting, pruning, or skipping pending tasks",
)
