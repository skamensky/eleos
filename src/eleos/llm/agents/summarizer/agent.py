from eleos.db.views.models import ToolSummaryInputView
from eleos.llm.agents.base.enums import SystemPrompt
from eleos.llm.agents.base.structured_agent import StructuredAgent, make_agent
from eleos.models.agents.summarizer.models import ToolSummaryOutput
from eleos.settings.config import config

tool_summarizer_agent: StructuredAgent[ToolSummaryInputView, ToolSummaryOutput] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.SUMMARIZER_TOOL,
    input_model=ToolSummaryInputView,
    output_model=ToolSummaryOutput,
    output_name="tool_summary",
    output_description="Normalized evidence summary",
)
