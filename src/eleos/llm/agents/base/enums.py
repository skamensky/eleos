from enum import StrEnum


class LlmModel(StrEnum):
    OPENAI_GPT_5_2 = "openai:gpt-5.2"


class SystemPrompt(StrEnum):
    CRITIC = "critic/system.j2"
    CLASSIFIER = "classifier/system.j2"
    SUMMARIZER_TOOL = "summarizer/tool_summary.j2"
    PLANNER_HYPOTHESIS_SEED = "planner/seed_hypotheses.j2"
    PLANNER_TASK_SEED = "planner/seed_tasks.j2"
    PLANNER_HYPOTHESIS_UPDATE = "planner/update_hypotheses.j2"
    PLANNER_FOLLOWUP_TASK = "planner/followup_task.j2"
    PLANNER_REPLAN_TASK = "planner/replan_task.j2"
    PLANNER_RAW_DETAIL = "planner/raw_detail.j2"
    PLANNER_TASK_SELECTION = "planner/task_selection.j2"
    TERMINATION_COMPLETION_CHECK = "termination/completion_check.j2"
    REPORTER_SYNTHESIS = "reporter/system.j2"
