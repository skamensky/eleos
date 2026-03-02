from pydantic import BaseModel


class CompletionCheckDecision(BaseModel):
    passed: bool
    reason: str
