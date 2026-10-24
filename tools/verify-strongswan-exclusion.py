#!/usr/bin/env python3
"""Record exact-ROMFS absence when the WR profile defers StrongSwan."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("trunk", type=Path)
parser.add_argument("profile", type=Path)
parser.add_argument("report", type=Path)
args = parser.parse_args()

effective = (args.trunk / ".config").read_text(encoding="utf-8").splitlines()
requested = args.profile.read_text(encoding="utf-8").splitlines()
romfs = args.trunk / "romfs"
forbidden = (
    "usr/sbin/ipsec",
    "usr/libexec/ipsec/_updown",
    "usr/libexec/ipsec/charon",
    "usr/libexec/ipsec/starter",
    "usr/libexec/ipsec/stroke",
    "usr/lib/ipsec/libstrongswan.so.0",
    "usr/lib/ipsec/libcharon.so.0",
)
checks = {
    "profile_excludes_strongswan": not any(
        line.startswith("CONFIG_FIRMWARE_INCLUDE_SSWAN=")
        and line.split("=", 1)[1] in ("y", "m") for line in requested
    ),
    "effective_config_excludes_strongswan": not any(
        line.startswith("CONFIG_FIRMWARE_INCLUDE_SSWAN=")
        and line.split("=", 1)[1] in ("y", "m") for line in effective
    ),
}
selected = any(
    line.startswith("CONFIG_FIRMWARE_INCLUDE_SSWAN=")
    and line.split("=", 1)[1] in ("y", "m") for line in requested
)
for name in forbidden:
    path = romfs / name
    checks["absent:" + name] = not path.exists() and not path.is_symlink()

report = {
    "schema": 1,
    "selected": selected,
    "image_verified": all(checks.values()),
    "runtime_verified": False,
    "scope": "StrongSwan excluded from requested and effective profile and forbidden userspace files absent from final ROMFS; XFRM kernel support is separate",
    "checks": checks,
    "success": all(checks.values()),
}
args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
if not report["success"]:
    raise SystemExit("StrongSwan exclusion image checks failed: " + ", ".join(
        key for key, passed in checks.items() if not passed
    ))
print("PASS StrongSwan is excluded from profile and final ROMFS")
