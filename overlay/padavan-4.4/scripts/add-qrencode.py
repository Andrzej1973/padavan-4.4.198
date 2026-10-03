#!/usr/bin/env python3
"""Connect the requested qrencode CLI to the pinned Padavan 4.4 build."""
from pathlib import Path
import sys

root = Path(sys.argv[1]) / "trunk"
libs = root / "libs/Makefile"
text = libs.read_text()
anchor = "all: $(patsubst %,%_only,$(dir_y))"
if text.count(anchor) != 1 or "CONFIG_FIRMWARE_INCLUDE_QRENCODE" in text:
    raise SystemExit("Unexpected qrencode build-hook state")
text = text.replace(anchor,
    "dir_$(CONFIG_FIRMWARE_INCLUDE_QRENCODE) += libqrencode\n\n" + anchor)
libs.write_text(text)
template = root / "configs/templates/WR1200JS.config"
text = template.read_text()
if "CONFIG_FIRMWARE_INCLUDE_QRENCODE" in text:
    raise SystemExit("Unexpected qrencode template state")
template.write_text(text.rstrip() + "\n\nCONFIG_FIRMWARE_INCLUDE_QRENCODE=n\n")
