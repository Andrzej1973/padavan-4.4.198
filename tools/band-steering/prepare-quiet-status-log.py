#!/usr/bin/env python3
"""Demote periodic MT7603 steering status logs; preserve protocol messages."""
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
lines[i] = lines[i].replace("DBG_LVL_OFF", "DBG_LVL_TRACE", 1)
target.write_text("".join(lines), encoding="utf-8")
print("Periodic MT7603 steering status log uses TRACE; protocol polling unchanged")
