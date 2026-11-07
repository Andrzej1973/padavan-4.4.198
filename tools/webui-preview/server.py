#!/usr/bin/env python3
"""Loopback-only, read-only Padavan Modern homepage preview."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
SOURCE_TREE = os.environ.get("PADAVAN_PREVIEW_SOURCE_TREE")
if SOURCE_TREE:
    STATIC_ROOT = Path(SOURCE_TREE).resolve() / "trunk" / "user" / "www"
    PUBLIC = STATIC_ROOT / "modern"
    DATA = Path(
        os.environ.get("PADAVAN_PREVIEW_DATA", ROOT / "data" / "dashboard.json")
    ).resolve()
    MODE = "read-only-production-shell"
else:
    STATIC_ROOT = ROOT / "public"
    PUBLIC = ROOT / "public"
    DATA = ROOT / "data" / "dashboard.json"
    MODE = "read-only-demo"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PADAVAN_PREVIEW_PORT", "8080"))


class PreviewHandler(BaseHTTPRequestHandler):
    server_version = "PadavanPreview/1.0"
    sys_version = ""

    def _headers(self, status: int, content_type: str, length: int, allow: str | None = None) -> None:
        self.send_response(status)
        if allow is not None:
            self.send_header("Allow", allow)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()

    def _send(self, status: int, payload: bytes, content_type: str) -> None:
        self._headers(status, content_type, len(payload))
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _not_allowed(self) -> None:
        body = b"Read-only preview: this HTTP method is blocked.\n"
        self._headers(405, "text/plain; charset=utf-8", len(body), "GET, HEAD")
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            self._send(403, b"Loopback clients only.\n", "text/plain; charset=utf-8")
            return

        route = urlsplit(self.path).path
        if route == "/__health":
            payload = json.dumps({"status": "ok", "mode": MODE}).encode("utf-8") + b"\n"
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if route in ("/", "/modern", "/modern/", "/modern/index.html"):
            path = PUBLIC / "index.html"
        elif route in ("/api/dashboard.json", "/wr_modern.json"):
            path = DATA
        elif route == "/shared-wifi.js":
            if SOURCE_TREE:
                path = PUBLIC / "shared-wifi.js"
            else:
                path = ROOT.parent / "shared-wifi" / "ui.js"
        else:
            relative = route.lstrip("/")
            path = (STATIC_ROOT / relative).resolve()
            try:
                path.relative_to(STATIC_ROOT.resolve())
            except ValueError:
                self._send(404, b"Not found.\n", "text/plain; charset=utf-8")
                return

        if not path.is_file():
            self._send(404, b"Not found.\n", "text/plain; charset=utf-8")
            return
        suffix = path.suffix.lower()
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".svg": "image/svg+xml",
        }.get(suffix, "application/octet-stream")
        self._send(200, path.read_bytes(), content_type)

    def do_HEAD(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self.do_GET()

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._not_allowed()

    def do_PUT(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._not_allowed()

    def do_PATCH(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._not_allowed()

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._not_allowed()

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stdout.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))
        sys.stdout.flush()


def serve() -> None:
    try:
        server = ThreadingHTTPServer((HOST, PORT), PreviewHandler)
    except OSError as exc:
        print(f"Cannot start preview on http://{HOST}:{PORT}/: {exc}", file=sys.stderr)
        print("If the port is busy, close the other local server or set PADAVAN_PREVIEW_PORT to another port.", file=sys.stderr)
        raise SystemExit(2) from exc
    server.daemon_threads = True
    if SOURCE_TREE:
        print(f"Padavan Modern production-shell fixture: http://{HOST}:{PORT}/modern/index.html", flush=True)
        print("Loopback only. Static production assets with live-JSON fixture; no router connection.", flush=True)
    else:
        print(f"Padavan Modern local DEMO: http://{HOST}:{PORT}/modern/", flush=True)
        print("Loopback only. GET/HEAD only; router actions and CGI are not available.", flush=True)
    print("Press Ctrl+C in this console to stop the preview.", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("Stopping local preview…", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
