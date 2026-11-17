#!/usr/bin/env python3
"""Compile actual store/guard/snapshot with native NVRAM syscall actors."""
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
shared = here.parent / "band-steering"
with tempfile.TemporaryDirectory(prefix="wr-saved-store-") as directory:
    root = Path(directory)
    (root / "rc.h").write_text(
        "int nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n"
    )
    (root / "wr-band-settings-snapshot.h").write_bytes((shared / "settings-snapshot.h").read_bytes())
    for prepared in (0, 1):
        binary = root / ("check-" + str(prepared))
        subprocess.run([
        "gcc", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-O2",
        "-fsanitize=address,undefined", "-fno-pie", "-no-pie",
        '-DWR_IOT_SERVICE_LOCK_PATH="' + str(root / "lock") + '"',
        "-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=" + str(prepared),
        "-I" + str(root), "-I" + str(here),
        str(here / "saved-config-store.c"), str(here / "service-guard.c"),
        str(shared / "settings-snapshot.c"), str(here / "check-saved-config-store.c"),
        "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True, timeout=15)
