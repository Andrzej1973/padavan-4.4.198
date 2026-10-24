#!/usr/bin/env python3
"""Require the unsupported optional CPU watchdog to be absent from WR1200JS UI/image."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("romfs", type=Path)
args = parser.parse_args()
root = args.romfs
page_path = root / "www/Advanced_Services_Content.asp"
page = page_path.read_text(encoding="utf-8")
if 'id="watchdog_cpu_on_of"' in page or "init_itoggle('watchdog_cpu')" in page:
    raise SystemExit("Unsupported WR1200JS CPU watchdog control remains in the image")
nav_start = page.find('id="wr_services_nav"')
if nav_start < 0:
    raise SystemExit("Unified services navigation is missing")
nav_begin = page.rfind("<nav ", 0, nav_start)
nav_end = page.find("</nav>", nav_begin)
if nav_begin < 0 or nav_end < 0:
    raise SystemExit("Cannot identify the unified services navigation")
nav = page[nav_begin:nav_end + len("</nav>")]
if "WRServicesNavWatchdog" in nav or "watchdog_cpu_on_of" in nav:
    raise SystemExit("Unsupported CPU watchdog is still linked in the image navigation")

modules = list(root.rglob("rt_timer_wdg.ko"))
if modules:
    raise SystemExit("Unsupported rt_timer_wdg module was packaged: " + ", ".join(map(str, modules)))

rc_path = root / "sbin/rc"
if not rc_path.is_file():
    raise SystemExit("Cannot locate the shipped /sbin/rc for CPU watchdog lifecycle verification")
rc = rc_path.read_bytes()
if b"rt_timer_wdg" in rc:
    raise SystemExit("Shipped rc still attempts to load or unload rt_timer_wdg")

print("PASS WR1200JS image hides the CPU watchdog control/link, omits rt_timer_wdg.ko, and ships inert rc lifecycle; built-in MT7621 watchdog is unaffected")
