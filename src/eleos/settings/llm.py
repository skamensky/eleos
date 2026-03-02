from pydantic import BaseModel

from eleos.llm.agents.base.enums import LlmModel


class LlmConfig(BaseModel):
    model: LlmModel = LlmModel.OPENAI_GPT_5_2
    base_url: str = "https://api.openai.com/v1"
