# LLM Agents Conventions

This directory defines the runtime side of typed LLM agents.
Associated typed inputs/outputs live in `src/eleos/models/agents/*`.

## Goals
- Keep agent integrations strongly typed and easy to repeat.
- Keep module boundaries obvious.
- Avoid boilerplate spread across many files.

## Directory Structure

```text
src/eleos/
  llm/agents/
    base/
      enums.py              # shared enums: model IDs + prompt IDs
      structured_agent.py   # generic StructuredAgent + make_agent(...)

    <agent_name>/
      agent.py              # get_<agent_name>_agent()

  llm/prompts/
    base/
      system.j2             # shared system template
    <agent_name>/
      system.j2             # agent prompt template extending base/system.j2

  models/agents/
    <agent_name>/
      models.py             # typed input/output pydantic models
```

## Rules

1. Keep all `__init__.py` files empty.
2. No barrel imports.
3. Use existing domain models in agent input models whenever possible.
4. Create new "input snapshot" models only when the existing models are too broad or leak irrelevant fields.
5. Put model and system prompt enums in `llm/agents/base/enums.py`.
6. Avoid partial-update cloning APIs for state transitions; construct explicit typed objects instead.
7. Use `make_agent(...)` so callers specify typed input/output model classes once while runtime still receives concrete schema types.
8. Use `NativeOutput(..., strict=True)` for provider-native schema enforcement.
9. Prompts should describe agent purpose, decision policy, and quality bar.
10. Do not include schema-compliance instructions in prompts (runtime enforces schema).
11. Use Jinja templates for prompts and extend `llm/prompts/base/system.j2` for shared runtime context.

## Repeatable Implementation Steps

1. Add typed models at `models/agents/<agent_name>/models.py`.
2. Add `llm/prompts/<agent_name>/system.j2` extending `llm/prompts/base/system.j2`.
3. Add enum entries in `llm/agents/base/enums.py`.
4. Add `llm/agents/<agent_name>/agent.py` with `get_<agent_name>_agent()`.
5. Inject the agent into the owning runtime class in `core/*`.
6. Keep behavior fail-closed if the caller requires strict runtime guarantees.

## Minimal Pattern

```python
# llm/agents/<agent_name>/agent.py
from eleos.llm.agents.base.enums import LlmModel, SystemPrompt
from eleos.llm.agents.base.structured_agent import StructuredAgent, make_agent
from eleos.models.agents.<agent_name>.models import InputModel, OutputModel
from eleos.settings.config import config

agent: StructuredAgent[InputModel, OutputModel] = make_agent(
    model=config.llm.model,
    prompt_id=SystemPrompt.<AGENT_PROMPT>,
    input_model=InputModel,
    output_model=OutputModel,
    output_name="<output_name>",
    output_description="<output_description>",
)
```
