#!/usr/bin/env python3
"""Enable the matching Linux 4.4 USBIP userspace and its libudev dependency."""
from pathlib import Path
import sys
root = Path(sys.argv[1]) / "trunk"
for file, entry in (
    ("libs/Makefile", "dir_$(CONFIG_FIRMWARE_INCLUDE_USBIP) += libudev"),
    ("user/Makefile", "dir_$(CONFIG_FIRMWARE_INCLUDE_USBIP) += usbip"),
):
    path = root / file
    text = path.read_text()
    anchor = "all: $(patsubst %,%_only,$(dir_y))"
    if text.count(anchor) != 1 or entry in text:
        raise SystemExit(f"Unexpected USBIP build-hook state: {file}")
    path.write_text(text.replace(anchor, entry + "\n\n" + anchor))
path = root / "configs/templates/WR1200JS.config"
text = path.read_text()
if "CONFIG_FIRMWARE_INCLUDE_USBIP" in text:
    raise SystemExit("Unexpected USBIP selector state")
path.write_text(text.rstrip() + "\n\nCONFIG_FIRMWARE_INCLUDE_USBIP=n\n")
