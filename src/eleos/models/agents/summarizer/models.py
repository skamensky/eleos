from pydantic import BaseModel


class ToolSummaryOutput(BaseModel):
    summary: str
