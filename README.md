# JSON-Key-Sorter

Minimal deterministic Task App for recursively sorting JSON object keys alphabetically.
Stateless, predictable, and side-effect free.

## Job

Expose exactly one MCP tool that sorts keys in a JSON object, including nested objects.

## Tool behavior

- **Tool name:** `sort_json_keys`
- **Behavior:**
  1. Validate input.
  2. Sort JSON keys deterministically (nested objects included).
  3. Return `structuredContent.sorted_json`.
- **Determinism:** No randomness, no inference, no external calls, no persistence.

## Input schema

```json
{
  "name": "sort_json_keys",
  "arguments": {
    "b": 1,
    "a": 2
  }
}
```

```json
{
  "name": "sort_json_keys",
  "arguments": {
    "z": {
      "b": 1,
      "a": 2
    },
    "a": 3
  }
}
```

## Output schema

```json
{
  "structuredContent": {
    "sorted_json": {
      "a": 2,
      "b": 1
    }
  }
}
```

```json
{
  "structuredContent": {
    "sorted_json": {
      "a": 3,
      "z": {
        "a": 2,
        "b": 1
      }
    }
  }
}
```

## Error schema

```json
{
  "name": "sort_json_keys",
  "arguments": {
    "json": "hello"
  }
}
```

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Input must be a JSON object (or wrapped as {'json': {...}})."
  }
}
```

## Routes

- `POST /tools/list`
- `POST /tools/call`
- `GET /health`
- `GET /privacy`
- `GET /terms`
- `GET /support`
- `GET /challenge`
