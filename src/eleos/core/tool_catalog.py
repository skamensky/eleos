from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from eleos.settings.config import config
from eleos.settings.tools import ToolCatalogEntryConfig


@dataclass(frozen=True)
class ToolCatalogEntry:
    tool_name: str
    function_description: str
    source_definition: str | None
    input_schema: dict[str, object]
    input_field_map: dict[str, str]


@dataclass(frozen=True)
class ToolCatalog:
    by_tool_name: dict[str, ToolCatalogEntry]

    def get(self, tool_name: str) -> ToolCatalogEntry | None:
        return self.by_tool_name.get(tool_name)


_tool_catalog: ToolCatalog | None = None


def get_tool_catalog() -> ToolCatalog:
    global _tool_catalog
    if _tool_catalog is None:
        _tool_catalog = _load_tool_catalog()
    return _tool_catalog


def _load_tool_catalog() -> ToolCatalog:
    entries: list[ToolCatalogEntryConfig] = list(config.tools.catalog_entries)
    if config.tools.catalog_path is not None:
        entries.extend(_load_entries_from_toml(Path(config.tools.catalog_path)))
    by_name: dict[str, ToolCatalogEntry] = {}
    for entry in entries:
        by_name[entry.tool_name] = ToolCatalogEntry(
            tool_name=entry.tool_name,
            function_description=entry.function_description,
            source_definition=entry.source_definition,
            input_schema={str(key): value for key, value in entry.input_schema.items()},
            input_field_map={str(key): str(value) for key, value in entry.input_field_map.items()},
        )
    return ToolCatalog(by_tool_name=by_name)


def _load_entries_from_toml(path: Path) -> list[ToolCatalogEntryConfig]:
    if not path.exists():
        raise FileNotFoundError(f"tool catalog file not found: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    raw_entries = data.get("tool")
    if not isinstance(raw_entries, list):
        raise ValueError("tool catalog must contain [[tool]] entries")
    entries: list[ToolCatalogEntryConfig] = []
    for index, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            raise ValueError(f"invalid tool catalog entry at index {index}")
        entries.append(ToolCatalogEntryConfig.model_validate(raw_entry))
    return entries
