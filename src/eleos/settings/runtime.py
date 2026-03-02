from pydantic import BaseModel, Field


class ThresholdConfig(BaseModel):
    confidence_sufficient: float = 0.8
    no_novelty_floor: float = 0.2
    expected_value_floor: float = 0.15


class RuntimeConfig(BaseModel):
    default_timeout_minutes: int = 120
    max_iterations: int = 80
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
