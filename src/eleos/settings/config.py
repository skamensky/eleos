from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from eleos.settings.classification import ClassificationConfig
from eleos.settings.llm import LlmConfig
from eleos.settings.persistence import PostgresPersistenceConfig
from eleos.settings.runtime import RuntimeConfig
from eleos.settings.tools import ToolConfig


class Config(BaseSettings):
    llm: LlmConfig = LlmConfig()
    runtime: RuntimeConfig = RuntimeConfig()
    persistence: PostgresPersistenceConfig = PostgresPersistenceConfig()
    tools: ToolConfig = ToolConfig()
    classification: ClassificationConfig = ClassificationConfig()

    model_config = SettingsConfigDict(env_nested_delimiter="__", env_prefix="ELEOS_")

    @model_validator(mode="after")
    def validate_classification_tool_references(self) -> "Config":
        servers = {server.server_id: server for server in self.tools.mcp_servers}
        errors: list[str] = []
        for category in self.classification.categories:
            references = category.required_tool_references + category.suggested_tool_references
            for reference in references:
                server_id, tool_name = reference.split("/", maxsplit=1)
                server = servers.get(server_id)
                if server is None:
                    errors.append(
                        "category "
                        f"'{category.category_id}' references unknown MCP server '{server_id}'"
                    )
                    continue
                if not server.enabled:
                    errors.append(
                        "category "
                        f"'{category.category_id}' references disabled MCP server '{server_id}'"
                    )
                    continue
                declared = set(server.declared_tools) | set(server.include_tools)
                if tool_name not in declared:
                    errors.append(
                        "category "
                        f"'{category.category_id}' references unknown tool "
                        f"'{tool_name}' for server "
                        f"'{server_id}'; add it to declared_tools/include_tools"
                    )
        if errors:
            raise ValueError("; ".join(errors))
        return self


config = Config()
