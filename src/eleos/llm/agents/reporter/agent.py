from eleos.db.views.models import ReportSynthesisInputView
from eleos.llm.agents.base.enums import SystemPrompt
from eleos.llm.agents.base.structured_agent import StructuredAgent, make_agent
from eleos.models.agents.reporter.models import ReportSynthesisOutput
from eleos.settings.config import config

report_synthesis_agent: StructuredAgent[
    ReportSynthesisInputView,
    ReportSynthesisOutput,
] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.REPORTER_SYNTHESIS,
    input_model=ReportSynthesisInputView,
    output_model=ReportSynthesisOutput,
    output_name="report_synthesis",
    output_description="Final report narrative and follow-up recommendations",
)
