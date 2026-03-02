from __future__ import annotations

from enum import StrEnum
from typing import Any, Generic, Mapping, TypeVar, cast

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.output import NativeOutput
from pydantic_ai.providers.openai import OpenAIProvider

from eleos.llm.agents.base.enums import LlmModel
from eleos.llm.prompts.loader import load_prompt
from eleos.settings.config import config

InModelT = TypeVar("InModelT", bound=BaseModel)
OutModelT = TypeVar("OutModelT", bound=BaseModel)


class StructuredAgent(Generic[InModelT, OutModelT]):
    def __init__(
        self,
        *,
        model: LlmModel,
        prompt_id: StrEnum,
        prompt_context: Mapping[str, Any] | None = None,
        input_model: type[InModelT],
        output_model: type[OutModelT],
        output_name: str,
        output_description: str,
    ) -> None:
        self._input_model = input_model
        resolved_model: str | OpenAIResponsesModel = _resolve_model(model)
        self._agent = Agent(
            resolved_model,
            instructions=load_prompt(prompt_id, context=prompt_context),
            output_type=NativeOutput(
                output_model,
                name=output_name,
                description=output_description,
                strict=True,
            ),
        )

    def run(self, payload: InModelT) -> OutModelT:
        if not isinstance(payload, self._input_model):
            raise TypeError(
                "invalid agent input type; expected "
                f"{self._input_model.__name__}, got {type(payload).__name__}"
            )
        payload_json = payload.model_dump_json(indent=2)
        result = self._agent.run_sync(payload_json)
        return cast(OutModelT, result.output)


def make_agent(
    *,
    model: LlmModel,
    prompt_id: StrEnum,
    prompt_context: Mapping[str, Any] | None = None,
    input_model: type[InModelT],
    output_model: type[OutModelT],
    output_name: str,
    output_description: str,
) -> StructuredAgent[InModelT, OutModelT]:
    # We centralize construction in a generic factory so call sites only provide
    # typed input/output model classes once while still giving the runtime the
    # concrete schema objects needed for strict provider-native validation.
    return StructuredAgent(
        model=model,
        prompt_id=prompt_id,
        prompt_context=prompt_context,
        input_model=input_model,
        output_model=output_model,
        output_name=output_name,
        output_description=output_description,
    )


def _resolve_model(model: LlmModel) -> str | OpenAIResponsesModel:
    # Keep OpenAI defaults zero-config while allowing OpenAI-compatible gateways
    # (e.g. LiteLLM) by overriding ELEOS_LLM__BASE_URL.
    model_value = model.value
    if not model_value.startswith("openai:"):
        return model_value

    model_name = model_value.split(":", maxsplit=1)[1]
    provider = OpenAIProvider(base_url=config.llm.base_url)
    return OpenAIResponsesModel(model_name, provider=provider)
