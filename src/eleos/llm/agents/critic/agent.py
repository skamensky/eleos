from eleos.db.views.models import CriticInputView
from eleos.llm.agents.base.enums import SystemPrompt
from eleos.llm.agents.base.structured_agent import StructuredAgent, make_agent
from eleos.models.agents.critic.models import CriticAssessment
from eleos.settings.config import config

critic_agent: StructuredAgent[CriticInputView, CriticAssessment] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.CRITIC,
    input_model=CriticInputView,
    output_model=CriticAssessment,
    output_name="critic_assessment",
    output_description="Assessment for whether investigation should replan now",
)
