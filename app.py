from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = "0.0.0.0"
PORT = 8000
TOOL_NAME = "sort_json_keys"


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
    def _set_headers(self, status: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        )
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()

    def _write_json(self, payload: dict[str, Any], status: int = 200) -> None:
        self._set_headers(status=status, content_type="application/json")
        self.wfile.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    def _write_text(self, text: str, status: int = 200) -> None:
        self._set_headers(status=status, content_type="text/plain; charset=utf-8")
        self.wfile.write(text.encode("utf-8"))

    def _error(self, code: str, message: str, status: int = 400) -> None:
        self._write_json({"error": {"code": code, "message": message}}, status=status)

    def _parse_json_body(self) -> Any:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def do_GET(self) -> None:
        if self.path == "/health":
            self._write_json({"status": "ok"})
            return
        if self.path == "/privacy":
            self._write_text("No data is stored. The app is stateless.")
            return
        if self.path == "/terms":
            self._write_text("Use as-is for deterministic JSON key sorting.")
            return
        if self.path == "/support":
            self._write_text("Support: open a repository issue.")
            return
        if self.path == "/challenge":
            self._write_text("json-key-sorter-challenge")
            return

        self._error("NOT_FOUND", "Route not found.", status=404)

    def do_POST(self) -> None:
        if self.path == "/tools/list":
            self._write_json(
                {
                    "tools": [
                        {
                            "name": TOOL_NAME,
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
                        }
                    ]
                }
            )
            return

        if self.path == "/tools/call":
            payload = self._parse_json_body()
            if not isinstance(payload, dict):
                self._error("INVALID_REQUEST", "Request body must be a JSON object.", status=400)
                return

            if payload.get("name") != TOOL_NAME:
                self._error("TOOL_NOT_FOUND", f"Unknown tool: {payload.get('name')}", status=404)
                return

            is_valid, json_object = _extract_json_input(payload.get("arguments"))
            if not is_valid:
                self._error(
                    "INVALID_INPUT",
                    "Input must be a JSON object (or wrapped as {'json': {...}}).",
                    status=400,
                )
                return

            self._write_json({"structuredContent": {"sorted_json": _sort_json_keys(json_object)}})
            return

        self._error("NOT_FOUND", "Route not found.", status=404)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving on http://{HOST}:{PORT}")
    server.serve_forever()
