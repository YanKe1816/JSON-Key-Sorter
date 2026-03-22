from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
APP_NAME = "JSON-Key-Sorter"
APP_VERSION = "1.0.0"
TASK_NAME = "sort_json_keys"
PROTOCOL_VERSION = "2024-11-05"

TOOL_DEFINITIONS = [
    {
        "name": "sort_json_keys",
        "description": "Sort keys of a JSON object alphabetically, including nested objects.",
        "inputSchema": {
            "oneOf": [
                {"type": "object", "description": "Raw JSON object to sort."},
                {
                    "type": "object",
                    "properties": {"json": {"type": "object"}},
                    "required": ["json"],
                    "additionalProperties": False,
                },
            ]
        },
        "outputShape": {"sorted_json": {}},
    }
]


def _sort_json_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sort_json_keys(value[key]) for key in sorted(value.keys())}
    if isinstance(value, list):
        return [_sort_json_keys(item) for item in value]
    return value


def _extract_json_input(arguments: Any) -> tuple[bool, Any]:
    if not isinstance(arguments, dict):
        return False, None

    if "json" in arguments and len(arguments) == 1:
        if isinstance(arguments["json"], dict):
            return True, arguments["json"]
        return False, None

    return True, arguments


class Handler(BaseHTTPRequestHandler):
    def _respond(self, status: int, payload: Any = None, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none';",
        )
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        if payload is None:
            return

        if content_type.startswith("application/json"):
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        else:
            body = str(payload).encode("utf-8")
        self.wfile.write(body)

    def _error(self, code: str, message: str, status: int = 400, rpc_id: Any | None = None) -> None:
        error_payload = {"error": {"code": code, "message": message}}
        if rpc_id is not None:
            self._respond(status, {"jsonrpc": "2.0", "id": rpc_id, **error_payload})
            return
        self._respond(status, error_payload)

    def _parse_json_body(self) -> Any:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def _manifest(self) -> dict[str, Any]:
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "task": TASK_NAME,
            "tools": TOOL_DEFINITIONS,
        }

    def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any] | tuple[str, str]:
        tool_name = params.get("name")
        if tool_name != TASK_NAME:
            return ("TOOL_NOT_FOUND", f"Unknown tool: {tool_name}")

        is_valid, json_object = _extract_json_input(params.get("arguments"))
        if not is_valid:
            return ("INVALID_INPUT", "Input must be a JSON object (or wrapped as {'json': {...}}).")

        sorted_json = _sort_json_keys(json_object)
        return {
            "content": [{"type": "text", "text": "JSON keys sorted successfully."}],
            "structuredContent": {"sorted_json": sorted_json},
        }

    def do_OPTIONS(self) -> None:
        try:
            self._respond(204)
        except Exception:
            self._error("INTERNAL_ERROR", "Internal server error.", status=500)

    def do_GET(self) -> None:
        try:
            if self.path == "/health":
                self._respond(200, {"status": "ok"})
                return
            if self.path == "/privacy":
                self._respond(200, "No data is stored. The app is stateless.", "text/plain; charset=utf-8")
                return
            if self.path == "/terms":
                self._respond(200, "Use as-is for deterministic JSON key sorting.", "text/plain; charset=utf-8")
                return
            if self.path == "/support":
                self._respond(200, "Support: open a repository issue.", "text/plain; charset=utf-8")
                return
            if self.path == "/.well-known/openai-apps-challenge":
                self._respond(200, os.environ.get("OPENAI_APPS_CHALLENGE", ""), "text/plain; charset=utf-8")
                return
            if self.path == "/mcp":
                self._respond(200, self._manifest())
                return

            self._error("NOT_FOUND", "Route not found.", status=404)
        except Exception:
            self._error("INTERNAL_ERROR", "Internal server error.", status=500)

    def do_POST(self) -> None:
        try:
            if self.path == "/tools/list":
                self._respond(200, {"tools": TOOL_DEFINITIONS})
                return

            if self.path == "/tools/call":
                payload = self._parse_json_body()
                if not isinstance(payload, dict):
                    self._error("INVALID_REQUEST", "Request body must be a JSON object.", status=400)
                    return

                result = self._handle_tools_call(payload)
                if isinstance(result, tuple):
                    code, message = result
                    self._error(code, message, status=400 if code == "INVALID_INPUT" else 404)
                    return

                self._respond(200, result)
                return

            if self.path == "/mcp":
                payload = self._parse_json_body()
                if not isinstance(payload, dict):
                    self._error("INVALID_REQUEST", "Request body must be a JSON-RPC object.", status=400)
                    return

                rpc_id = payload.get("id")
                method = payload.get("method")
                params = payload.get("params") if isinstance(payload.get("params"), dict) else {}

                if method == "initialize":
                    self._respond(
                        200,
                        {
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "result": {
                                "protocolVersion": PROTOCOL_VERSION,
                                "serverInfo": {"name": APP_NAME, "version": APP_VERSION},
                            },
                        },
                    )
                    return

                if method == "notifications/initialized":
                    self._respond(200, {"jsonrpc": "2.0", "id": rpc_id, "result": {}})
                    return

                if method == "tools/list":
                    self._respond(200, {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOL_DEFINITIONS}})
                    return

                if method == "tools/call":
                    result = self._handle_tools_call(params)
                    if isinstance(result, tuple):
                        code, message = result
                        self._error(code, message, status=400 if code == "INVALID_INPUT" else 404, rpc_id=rpc_id)
                        return
                    self._respond(200, {"jsonrpc": "2.0", "id": rpc_id, "result": result})
                    return

                self._error("METHOD_NOT_FOUND", f"Unsupported method: {method}", status=404, rpc_id=rpc_id)
                return

            self._error("NOT_FOUND", "Route not found.", status=404)
        except Exception:
            self._error("INTERNAL_ERROR", "Internal server error.", status=500)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving on http://{HOST}:{PORT}")
    server.serve_forever()
