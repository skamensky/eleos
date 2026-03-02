# MCP Supabase Example

Example MCP-compatible HTTP service exposing:

- `log_scan`
- `function_runs`
- `auth_timeline`
- `access_path_explain`
- `metadata_api_inspect`
- `sql_readonly`

Endpoint:
- `POST /invoke`

Request shape:

```json
{
  "tool_name": "log_scan",
  "payload": {},
  "tool_definition": {
    "tool_name": "supabase/log_scan",
    "function_description": "...",
    "source_definition": "...",
    "input_schema": {}
  }
}
```
