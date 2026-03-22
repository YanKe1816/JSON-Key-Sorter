# JSON-Key-Sorter

Stateless MCP-compatible Task App that deterministically sorts JSON object keys alphabetically.
Sorting is recursive for nested objects and preserves values exactly.

## Task

Expose one tool, `sort_json_keys`, that validates input JSON and returns the same JSON with keys sorted alphabetically at every object level.

## Input

`tools/call` accepts either:

```json
{"name":"sort_json_keys","arguments":{"b":1,"a":2}}
```

or

```json
{"name":"sort_json_keys","arguments":{"json":{"b":1,"a":2}}}
```

## Output

`tools/call` returns:

```json
{
  "content": [{"type": "text", "text": "JSON keys sorted successfully."}],
  "structuredContent": {"sorted_json": {"a": 2, "b": 1}}
}
```

## Error contract

All errors return:

```json
{
  "error": {
    "code": "...",
    "message": "..."
  }
}
```

## MCP interface

### `GET /mcp`

Returns manifest:

```json
{
  "name": "JSON-Key-Sorter",
  "version": "1.0.0",
  "task": "sort_json_keys",
  "tools": [
    {
      "name": "sort_json_keys",
      "description": "Sort keys of a JSON object alphabetically, including nested objects.",
      "inputSchema": {
        "oneOf": [
          {"type": "object", "description": "Raw JSON object to sort."},
          {"type": "object", "properties": {"json": {"type": "object"}}, "required": ["json"], "additionalProperties": false}
        ]
      },
      "outputShape": {"sorted_json": {}}
    }
  ]
}
```

### `POST /mcp` (JSON-RPC)

Supported methods:
- `initialize` (returns `protocolVersion` and `serverInfo`)
- `notifications/initialized`
- `tools/list` (returns exact `TOOL_DEFINITIONS`)
- `tools/call` (returns `content` + `structuredContent.sorted_json`)

Example:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"sort_json_keys","arguments":{"z":{"b":1,"a":2},"a":3}}}
```

## Routes

- `GET /health`
- `GET /privacy`
- `GET /terms`
- `GET /support`
- `GET /.well-known/openai-apps-challenge`
- `GET /mcp`
- `POST /mcp`
- `POST /tools/list`
- `POST /tools/call`
- `OPTIONS *`

## Deploy

```bash
PORT=8000 OPENAI_APPS_CHALLENGE=your-token python server.py
```

## cURL examples

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/.well-known/openai-apps-challenge
curl -s http://localhost:8000/mcp
curl -s http://localhost:8000/mcp -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
curl -s http://localhost:8000/mcp -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
curl -s http://localhost:8000/mcp -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"sort_json_keys","arguments":{"b":1,"a":2}}}'
```

## ChatGPT add-app instructions

1. Deploy to an HTTPS URL.
2. Configure ChatGPT app endpoint to `${BASE_URL}/mcp`.
3. Confirm `tools/list` returns one tool: `sort_json_keys`.
4. Run `tools/call` and verify deterministic sorted output.
