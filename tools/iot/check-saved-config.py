#!/usr/bin/env python3
"""Exercise provisioning validation with host sanitizers; no NVRAM writes."""
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="wr-saved-config-") as directory:
    binary = Path(directory) / "check"
    subprocess.run([
        "gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
        "-fsanitize=address,undefined", "-fno-pie", "-no-pie",
        "-I" + str(here), str(here / "check-saved-config.c"), "-o", str(binary),
    ], check=True)
    subprocess.run([str(binary)], check=True, timeout=15)
