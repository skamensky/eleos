from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class McpTransportType(str, Enum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable_http"


class McpBearerTokenAuthConfig(BaseModel):
    type: Literal["bearer_token"] = "bearer_token"
    token_env_var: str


class McpOAuthClientCredentialsAuthConfig(BaseModel):
    type: Literal["oauth_client_credentials"] = "oauth_client_credentials"
    token_url: str
    client_id: str
    client_secret_env_var: str
    scopes: list[str] = Field(default_factory=list)
    audience: str | None = None
    extra_token_request_params: dict[str, str] = Field(default_factory=dict)


McpAuthConfig = Annotated[
    McpBearerTokenAuthConfig | McpOAuthClientCredentialsAuthConfig,
    Field(discriminator="type"),
]


class McpStdioTransportConfig(BaseModel):
    type: Literal[McpTransportType.STDIO] = McpTransportType.STDIO
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    cwd: str | None = None


class McpStreamableHttpTransportConfig(BaseModel):
    type: Literal[McpTransportType.STREAMABLE_HTTP] = McpTransportType.STREAMABLE_HTTP
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    auth: McpAuthConfig | None = None
    connect_timeout_seconds: int = 5
    read_timeout_seconds: int = 30
    verify_tls: bool = True
    ca_bundle_path: str | None = None


McpTransportConfig = Annotated[
    McpStdioTransportConfig | McpStreamableHttpTransportConfig,
    Field(discriminator="type"),
]


class McpServerConfig(BaseModel):
    server_id: str
    enabled: bool = True
    transport: McpTransportConfig

    # Optional explicit registration for deterministic tool routing in playbooks.
    declared_tools: list[str] = Field(default_factory=list)
    include_tools: list[str] = Field(default_factory=list)
    exclude_tools: list[str] = Field(default_factory=list)
    tool_name_prefix: str | None = None
    allow_unscoped_tool_names: bool = False

    initialize_timeout_seconds: int = 10
    request_timeout_seconds: int = 30
    max_retries: int = 1
    retry_backoff_seconds: float = 0.2


class ToolCatalogEntryConfig(BaseModel):
    tool_name: str
    function_description: str
    source_definition: str | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)
    input_field_map: dict[str, str] = Field(default_factory=dict)


class ToolConfig(BaseModel):
    mcp_servers: list[McpServerConfig] = Field(default_factory=list)
    catalog_path: str | None = None
    catalog_entries: list[ToolCatalogEntryConfig] = Field(default_factory=list)
