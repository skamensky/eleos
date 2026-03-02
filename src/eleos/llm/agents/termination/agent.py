from eleos.db.views.models import CompletionCheckInputView
from eleos.llm.agents.base.enums import SystemPrompt
from eleos.llm.agents.base.structured_agent import StructuredAgent, make_agent
from eleos.models.agents.termination.models import CompletionCheckDecision
from eleos.settings.config import config

completion_check_agent: StructuredAgent[
    CompletionCheckInputView,
    CompletionCheckDecision,
] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.TERMINATION_COMPLETION_CHECK,
    input_model=CompletionCheckInputView,
    output_model=CompletionCheckDecision,
    output_name="completion_check_decision",
    output_description="Decision for whether a mandatory completion check is satisfied",
)
