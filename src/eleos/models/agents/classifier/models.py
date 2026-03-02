from pydantic import BaseModel, Field


class CaseClassificationOption(BaseModel):
    case_class: str
    description: str
    required_tool_references: list[str] = Field(default_factory=list)
    suggested_tool_references: list[str] = Field(default_factory=list)


class CaseClassificationInput(BaseModel):
    objective: str
    possible_classifications: list[CaseClassificationOption] = Field(default_factory=list)
