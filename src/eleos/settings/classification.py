from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


class ClassificationCategoryConfig(BaseModel):
    category_id: str
    description: str
    required_tool_references: list[str] = Field(default_factory=list)
    suggested_tool_references: list[str] = Field(default_factory=list)

    @field_validator("category_id")
    @classmethod
    def validate_category_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("category_id must not be empty")
        return normalized

    @field_validator("required_tool_references", "suggested_tool_references")
    @classmethod
    def validate_tool_references(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            if "/" not in value:
                raise ValueError("tool reference must be 'server_id/tool_name'")
            server_id, tool_name = value.split("/", maxsplit=1)
            if not server_id or not tool_name:
                raise ValueError("tool reference must be 'server_id/tool_name'")
            normalized.append(value)
        return normalized


class ClassificationConfig(BaseModel):
    categories: list[ClassificationCategoryConfig] = Field(
        default_factory=lambda: [
            ClassificationCategoryConfig(
                category_id="incident",
                description=(
                    "Outages, reliability, latency, and service degradation investigations."
                ),
            ),
            ClassificationCategoryConfig(
                category_id="billing",
                description="Costs, invoices, charges, and spend anomaly investigations.",
            ),
            ClassificationCategoryConfig(
                category_id="general",
                description=(
                    "General or ambiguous support investigations that need baseline triage."
                ),
            ),
        ]
    )

    @model_validator(mode="after")
    def validate_unique_category_ids(self) -> "ClassificationConfig":
        seen: set[str] = set()
        duplicates: set[str] = set()
        for category in self.categories:
            if category.category_id in seen:
                duplicates.add(category.category_id)
            seen.add(category.category_id)
        if duplicates:
            duplicate_ids = ", ".join(sorted(duplicates))
            raise ValueError(f"duplicate classification category ids: {duplicate_ids}")
        return self
