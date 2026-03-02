from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def load_prompt(
    prompt_id: StrEnum,
    context: Mapping[str, Any] | None = None,
) -> str:
    prompts_root = Path(__file__).resolve().parent
    env = Environment(
        loader=FileSystemLoader(str(prompts_root)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    template = env.get_template(prompt_id.value)
    return template.render(**(dict(context or {})))
