from pydantic import BaseModel, Field


class CriticAssessment(BaseModel):
    requires_replan: bool
    reason: str
    drift_score: float = Field(ge=0.0, le=1.0)
    novelty_score: float = Field(ge=0.0, le=1.0)
