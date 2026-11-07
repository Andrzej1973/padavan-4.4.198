#!/usr/bin/env python3
"""Verify owner-supplied Modern WebUI reference images without external tools."""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "docs/design/reference"
EXPECTED = {
    "dashboard-neon-uk-detailed.png": {
        "size": 1752014,
        "sha256": "a06fefb02d09d61d620db9c35e424c256a5cb46895f9e4b4b5793d8164379b84",
        "dimensions": (1312, 1199),
    },
    "dashboard-neon-uk.png": {
        "size": 1814723,
        "sha256": "b53d077079c35179fd7ca0478902f0f2150ad13a656b5eccfb4df08ac57fb520",
        "dimensions": (1536, 1024),
    },
    "wifi-bridge-24.png": {
        "size": 1590818,
        "sha256": "c6a6ef94307fd329f53fdaec23f6f9f4f531163a7a678ba0677b14257685f092",
        "dimensions": (1536, 1024),
    },
    "wifi-general-24.png": {
        "size": 1544711,
        "sha256": "b73622f2f4367a53c765fe26eeca4555e9df668d43bd38c21e7ee8771470f937",
        "dimensions": (1536, 1024),
    },
    "wifi-shared-settings.png": {
        "size": 1558783,
        "sha256": "c1394ebc7b34db172f7d090d7c4954e6555b5803e064de5f7194f75c48229b03",
        "dimensions": (1536, 1024),
    },
    "wifi-split-settings.png": {
        "size": 1542460,
        "sha256": "c06967e3b3cfcc26f31ef153c23984d8369e89787945bce415d207770a2c677b",
        "dimensions": (1536, 1024),
    },
}


def png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or data[12:16] != b"IHDR":
        raise ValueError("not a PNG with an IHDR chunk")
    return struct.unpack(">II", data[16:24])


def main() -> int:
    failures: list[str] = []
    actual_names = {path.name for path in REFERENCE_DIR.glob("*.png")}
    expected_names = set(EXPECTED)
    if actual_names != expected_names:
        failures.append(
            f"reference inventory differs: missing={sorted(expected_names - actual_names)} "
            f"extra={sorted(actual_names - expected_names)}"
        )

    for name, expected in EXPECTED.items():
        path = REFERENCE_DIR / name
        if not path.is_file():
            failures.append(f"{name}: missing")
            continue
        data = path.read_bytes()
        if len(data) != expected["size"]:
            failures.append(f"{name}: size {len(data)} != {expected['size']}")
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected["sha256"]:
            failures.append(f"{name}: SHA256 {digest} != {expected['sha256']}")
        try:
            dimensions = png_dimensions(data)
        except ValueError as error:
            failures.append(f"{name}: {error}")
        else:
            if dimensions != expected["dimensions"]:
                failures.append(
                    f"{name}: dimensions {dimensions} != {expected['dimensions']}"
                )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(f"PASS {len(EXPECTED)} owner-supplied Modern WebUI reference images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
