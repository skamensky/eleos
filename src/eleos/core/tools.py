from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from eleos.core.tool_catalog import ToolCatalog, get_tool_catalog
from eleos.models.payloads import ToolInputPayload
from eleos.models.tool_execution import ToolRunResult
from eleos.settings.config import config
from eleos.settings.tools import (
    McpBearerTokenAuthConfig,
    McpServerConfig,
    McpStdioTransportConfig,
    McpStreamableHttpTransportConfig,
)


@dataclass(frozen=True)
class McpToolRoute:
    server: McpServerConfig
    remote_tool_name: str


class McpToolRegistry:
    def __init__(self) -> None:
        self._catalog: ToolCatalog = get_tool_catalog()
        self._servers: dict[str, McpServerConfig] = {
            server.server_id: server
            for server in config.tools.mcp_servers
            if server.enabled
        }
        self._declared_routes: dict[str, McpToolRoute] = {}
        self._index_declared_routes()

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(0.05))
    def run(self, tool_name: str, payload: ToolInputPayload) -> ToolRunResult:
        route = self._resolve_route(tool_name)
        if route is None:
            return ToolRunResult(
                source=tool_name,
                summary="Tool unavailable",
                raw_payload={"error": f"unknown MCP tool: {tool_name}"},
                failed=True,
                error=f"unknown MCP tool: {tool_name}",
            )
        return self._invoke_mcp_tool(route, payload)

    def _index_declared_routes(self) -> None:
        for server in self._servers.values():
            for remote_tool_name in server.declared_tools:
                route_name = self._declared_route_name(server, remote_tool_name)
                self._declared_routes[route_name] = McpToolRoute(
                    server=server,
                    remote_tool_name=remote_tool_name,
                )

    def _declared_route_name(self, server: McpServerConfig, remote_tool_name: str) -> str:
        if server.tool_name_prefix is not None:
            return f"{server.tool_name_prefix}{remote_tool_name}"
        return f"{server.server_id}/{remote_tool_name}"

    def _resolve_route(self, tool_name: str) -> McpToolRoute | None:
        declared = self._declared_routes.get(tool_name)
        if declared is not None and self._is_tool_allowed(
            declared.server,
            declared.remote_tool_name,
        ):
            return declared

        # Explicit namespace route: "<server_id>/<tool_name>".
        if "/" in tool_name:
            maybe_server_id, maybe_remote_name = tool_name.split("/", maxsplit=1)
            server = self._servers.get(maybe_server_id)
            if server is not None and self._is_tool_allowed(server, maybe_remote_name):
                return McpToolRoute(server=server, remote_tool_name=maybe_remote_name)

        # Optional unscoped route if exactly one server opts in.
        candidate_servers = [
            server
            for server in self._servers.values()
            if server.allow_unscoped_tool_names and self._is_tool_allowed(server, tool_name)
        ]
        if len(candidate_servers) == 1:
            return McpToolRoute(server=candidate_servers[0], remote_tool_name=tool_name)
        return None

    def _is_tool_allowed(self, server: McpServerConfig, remote_tool_name: str) -> bool:
        if server.include_tools and remote_tool_name not in server.include_tools:
            return False
        if remote_tool_name in server.exclude_tools:
            return False
        return True

    def _invoke_mcp_tool(self, route: McpToolRoute, payload: ToolInputPayload) -> ToolRunResult:
        transport = route.server.transport
        if isinstance(transport, McpStdioTransportConfig):
            return self._invoke_stdio(route, payload)
        if isinstance(transport, McpStreamableHttpTransportConfig):
            return self._invoke_streamable_http(route, payload)
        return ToolRunResult(
            source=f"mcp:{route.server.server_id}",
            summary="MCP transport unsupported",
            raw_payload={"error": f"unsupported transport: {transport.type}"},
            failed=True,
            error=f"unsupported transport: {transport.type}",
        )

    def _invoke_stdio(self, route: McpToolRoute, payload: ToolInputPayload) -> ToolRunResult:
        transport = route.server.transport
        if not isinstance(transport, McpStdioTransportConfig):
            raise TypeError("invalid stdio transport configuration")
        return ToolRunResult(
            source=f"mcp:{route.server.server_id}",
            summary="MCP stdio invocation not implemented in this sample refactor",
            raw_payload={
                "server_id": route.server.server_id,
                "tool_name": route.remote_tool_name,
                "transport": transport.type.value,
                "payload": payload,
            },
            failed=True,
            error="mcp_stdio_not_implemented",
        )

    def _invoke_streamable_http(
        self,
        route: McpToolRoute,
        payload: ToolInputPayload,
    ) -> ToolRunResult:
        transport = route.server.transport
        if not isinstance(transport, McpStreamableHttpTransportConfig):
            raise TypeError("invalid streamable_http transport configuration")
        headers = self._streamable_http_headers(route.server)
        headers.update(transport.headers)
        request_payload: dict[str, object] = {
            "tool_name": route.remote_tool_name,
            "payload": payload,
        }
        tool_definition = self._tool_definition(route)
        if tool_definition:
            request_payload["tool_definition"] = tool_definition
        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    connect=float(transport.connect_timeout_seconds),
                    read=float(transport.read_timeout_seconds),
                    write=float(transport.read_timeout_seconds),
                    pool=float(transport.connect_timeout_seconds),
                ),
                verify=self._verify_tls_setting(transport),
            ) as client:
                response = client.post(
                    transport.url,
                    json=request_payload,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return ToolRunResult(
                source=f"mcp:{route.server.server_id}",
                summary="MCP streamable_http invocation failed",
                raw_payload={
                    "server_id": route.server.server_id,
                    "tool_name": route.remote_tool_name,
                    "url": transport.url,
                    "error": str(exc),
                },
                failed=True,
                error=f"mcp_streamable_http_error: {exc}",
            )

        try:
            data = response.json()
        except ValueError as exc:
            return ToolRunResult(
                source=f"mcp:{route.server.server_id}",
                summary="MCP streamable_http returned non-JSON response",
                raw_payload={"error": str(exc)},
                failed=True,
                error="mcp_streamable_http_invalid_json",
            )

        return ToolRunResult(
            source=str(data.get("source", f"mcp:{route.server.server_id}")),
            summary=str(data.get("summary", "MCP tool executed")),
            raw_payload=_as_dict(data.get("raw_payload")),
            anomalies=_as_str_list(data.get("anomalies")),
            confidence_impact=float(data.get("confidence_impact", 0.0)),
            novelty_signal=float(data.get("novelty_signal", 0.0)),
            failed=bool(data.get("failed", False)),
            error=_as_optional_str(data.get("error")),
        )

    def _streamable_http_headers(self, server: McpServerConfig) -> dict[str, str]:
        headers = {"content-type": "application/json"}
        transport = server.transport
        if not isinstance(transport, McpStreamableHttpTransportConfig):
            return headers
        auth = transport.auth
        if isinstance(auth, McpBearerTokenAuthConfig):
            token = os.getenv(auth.token_env_var)
            if token:
                headers["authorization"] = f"Bearer {token}"
        return headers

    def _verify_tls_setting(self, transport: McpStreamableHttpTransportConfig) -> bool | str:
        if transport.ca_bundle_path is not None:
            return transport.ca_bundle_path
        return transport.verify_tls

    def _tool_definition(self, route: McpToolRoute) -> dict[str, object]:
        namespaced_name = f"{route.server.server_id}/{route.remote_tool_name}"
        candidates = (
            namespaced_name,
            route.remote_tool_name,
            self._declared_route_name(route.server, route.remote_tool_name),
        )
        for candidate in candidates:
            entry = self._catalog.get(candidate)
            if entry is None:
                continue
            return {
                "tool_name": entry.tool_name,
                "function_description": entry.function_description,
                "source_definition": entry.source_definition,
                "input_schema": entry.input_schema,
            }
        return {}


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _as_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


_mcp_tool_registry: McpToolRegistry | None = None


def get_mcp_tool_registry() -> McpToolRegistry:
    global _mcp_tool_registry
    if _mcp_tool_registry is None:
        _mcp_tool_registry = McpToolRegistry()
    return _mcp_tool_registry
