from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, create_model

from eleos.llm.agents.base.enums import SystemPrompt
from eleos.llm.agents.base.structured_agent import StructuredAgent, make_agent
from eleos.models.agents.classifier.models import CaseClassificationInput, CaseClassificationOption
from eleos.settings.classification import ClassificationCategoryConfig
from eleos.settings.config import config


class CaseClassificationOutputBase(BaseModel):
    case_class: str


def classify_case(objective: str) -> str:
    categories = config.classification.categories
    if not categories:
        raise ValueError("classification categories must not be empty")

    case_classes = tuple(category.category_id for category in categories)
    payload = CaseClassificationInput(
        objective=objective,
        possible_classifications=_classification_options(categories),
    )
    agent = _get_case_classifier(case_classes)
    result = agent.run(payload)
    return result.case_class


def _classification_options(
    categories: list[ClassificationCategoryConfig],
) -> list[CaseClassificationOption]:
    options: list[CaseClassificationOption] = []
    for category in categories:
        options.append(
            CaseClassificationOption(
                case_class=category.category_id,
                description=category.description,
                required_tool_references=list(category.required_tool_references),
                suggested_tool_references=list(category.suggested_tool_references),
            )
        )
    return options


@lru_cache(maxsize=16)
def _get_case_classifier(
    case_classes: tuple[str, ...],
) -> StructuredAgent[CaseClassificationInput, CaseClassificationOutputBase]:
    output_model = _build_case_class_output_model(case_classes)
    return make_agent(
        model=config.llm.model,
        prompt_id=SystemPrompt.CLASSIFIER,
        input_model=CaseClassificationInput,
        output_model=output_model,
        output_name="case_classification",
        output_description="Case class decision for routing playbook selection",
    )


def _build_case_class_output_model(
    case_classes: tuple[str, ...],
) -> type[CaseClassificationOutputBase]:
    case_class_type = Literal.__getitem__(case_classes)
    model_name = "CaseClassificationOutput__" + "__".join(case_classes)
    return create_model(
        model_name,
        __base__=CaseClassificationOutputBase,
        case_class=(case_class_type, ...),
    )
