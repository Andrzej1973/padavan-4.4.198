#!/usr/bin/env python3
"""Install the verified Modern IoT payload beside its isolated candidate httpd."""
import argparse
import hashlib
import json
from pathlib import Path

ASSETS = ("index.html", "wifi.js", "modern-iot.js")


def stage(romfs, candidate, report):
    if report.exists() or report.is_symlink():
        raise ValueError("Modern IoT ROMFS report already exists")
    metadata = json.loads((candidate / "modern-iot-candidate.json").read_text())
    if metadata.get("board") != "WR1200JS" or metadata.get("candidate_only") is not True:
        raise ValueError("Expected isolated WR1200JS Modern IoT candidate")
    linked = (candidate / "httpd").read_bytes()
    installed = romfs / "usr/sbin/httpd"
    if installed.is_symlink() or installed.read_bytes() != linked or b"modern/modern-iot.js\0" not in linked:
        raise ValueError("ROMFS httpd differs from the linked Modern IoT candidate")

    modern = romfs / "www/modern"
    if modern.is_symlink() or not modern.is_dir() or modern.parent.is_symlink():
        raise ValueError("Expected installed Modern WebUI")
    payload = {}
    hashes = {}
    for name in ASSETS:
        source = candidate / "modern" / name
        destination = modern / name
        if source.is_symlink() or destination.is_symlink():
            raise ValueError("Unexpected Modern asset symlink")
        if name == "modern-iot.js":
            if destination.exists():
                raise ValueError("Modern IoT controller already installed")
        elif not destination.is_file():
            raise ValueError("Missing Modern shell asset: " + name)
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != metadata["sha256"]["trunk/user/www/modern/" + name]:
            raise ValueError("Modern candidate hash mismatch: " + name)
        payload[destination] = data
        hashes["www/modern/" + name] = digest

    for destination, data in payload.items():
        destination.write_bytes(data)
    report.write_text(json.dumps({
        "board": "WR1200JS",
        "httpd_sha256": hashlib.sha256(linked).hexdigest(),
        "sha256": hashes,
        "trx_verified": False,
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("romfs", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    stage(args.romfs, args.candidate, args.report)
    print("PASS isolated Modern IoT ROMFS staging against the linked HTTP candidate")
