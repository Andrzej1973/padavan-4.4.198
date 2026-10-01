#!/usr/bin/env python3
"""Connect ndisc6/rdisc6 from the existing firmware overlay."""
from pathlib import Path
import sys

root = Path(sys.argv[1]) / "trunk"
user = root / "user/Makefile"
text = user.read_text()
anchor = "all: $(patsubst %,%_only,$(dir_y))"
if text.count(anchor) != 1 or "CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6" in text:
    raise SystemExit("Unexpected ndisc6 build-hook state")
user.write_text(text.replace(anchor,
    "dir_$(CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6) += ndisc6\n\n" + anchor))
template = root / "configs/templates/WR1200JS.config"
text = template.read_text()
if "CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6" in text:
    raise SystemExit("Unexpected ndisc6 template state")
template.write_text(text.rstrip() + "\n\nCONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6=n\n")
