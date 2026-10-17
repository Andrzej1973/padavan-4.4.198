#!/usr/bin/env python3
"""Remove the periodic MT7603 steering status log; preserve protocol messages."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("source", type=Path)
a = p.parse_args()
target = a.source / "trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_band_steering.c"
text = target.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
matched = [i for i, line in enumerate(lines) if "STATUS QUERY ON" in line and "BND_STRG_MTWF_LOG(" in line]
if len(matched) != 1:
    raise SystemExit("Expected exactly one MT7603 periodic steering status log")
i = matched[0]
if "DBG_LVL_OFF" not in lines[i]:
    raise SystemExit("Unexpected steering status log level; fresh source required")
indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
lines[i] = indent + "/* Periodic status log removed: it filled syslog without new information. */\n"
target.write_text("".join(lines), encoding="utf-8")
print("Removed the periodic MT7603 steering status log; protocol polling unchanged")
