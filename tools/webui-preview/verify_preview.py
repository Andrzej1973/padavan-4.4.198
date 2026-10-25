#!/usr/bin/env python3
"""HTTP and content checks for the local read-only preview (server must be running)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASE = f"http://127.0.0.1:{os.environ.get('PADAVAN_PREVIEW_PORT', '8080')}"


class LocalResources(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.resources: list[str] = []
        self.forms = 0
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "link" and values.get("href", "").startswith("/"):
            self.resources.append(values["href"] or "")
        if tag == "script" and values.get("src", "").startswith("/"):
            self.resources.append(values["src"] or "")
        if tag == "form":
            self.forms += 1
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")


def get(path: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(BASE + path, timeout=3) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def main() -> None:
    status, health = get("/__health")
    assert_equal(status, 200, "health endpoint")
    assert_equal(json.loads(health)["mode"], "read-only-demo", "preview mode")
    status, html = get("/modern/")
    assert_equal(status, 200, "Modern homepage")
    text = html.decode("utf-8")
    assert_equal('lang="uk"' in text, True, "Ukrainian UI")
    assert_equal("IoT 2.4" in text or "IoT 2,4" in text, False, "IoT exclusion until implementation is complete")
    assert_equal('id="modern-wifi"' in text, True, "isolated Modern Wi-Fi mount")
    parser = LocalResources()
    parser.feed(text)
    assert_equal(parser.forms, 0, "mutating forms")
    release_link = "https://github.com/Andrzej1973/padavan-4.4.198/releases"
    assert_equal(parser.links.count(release_link), 1, "single GitHub releases link")
    assert_equal(all((link.startswith("/") and not link.startswith("//")) or link == release_link for link in parser.links), True, "navigation links stay local except GitHub releases")
    assert_equal("footer-version" in text, False, "firmware version appears only in the header")
    for path in parser.resources:
        status, _ = get(path)
        assert_equal(status, 200, f"local resource {path}")
    status, wifi = get('/wifi-schema.json')
    assert_equal(status, 200, 'Wi-Fi demo schema')
    assert_equal(json.loads(wifi)['demo'], True, 'Wi-Fi schema demo marker')
    assert_equal(len(json.loads(wifi)['pages']), 2, 'two independent bands')
    status, data_bytes = get("/api/dashboard.json")
    assert_equal(status, 200, "demo data endpoint")
    data = json.loads(data_bytes)
    assert_equal(data.get("demo"), True, "DEMO marker")
    assert_equal(len(data.get("wifi", [])), 2, "Wi-Fi card count (IoT deferred)")
    assert_equal(len(data.get("serviceTiles", [])), 12, "configurable placeholder tile count")
    assert_equal(all(not tile.get("confirmed", True) for tile in data["serviceTiles"]), True, "service placeholders are explicitly unconfirmed")
    for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
        request = urllib.request.Request(BASE + "/", method=method, data=b"x" if method in ("POST", "PUT", "PATCH") else None)
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                code = response.status
        except urllib.error.HTTPError as exc:
            code = exc.code
        assert_equal(code, 405, f"server-side block for {method}")
    status, _ = get("/not-a-real-page.asp")
    assert_equal(status, 404, "unknown page")
    print("PASS: health, homepage, Ukrainian text, local assets, Wi-Fi demo schema, placeholders, no live IoT card, and one GitHub releases link.")
    print("PASS: POST, PUT, PATCH, DELETE and OPTIONS are rejected by the server (405).")
    print("PASS: unknown pages return 404; no fake Classic pages are served.")


if __name__ == "__main__":
    main()
