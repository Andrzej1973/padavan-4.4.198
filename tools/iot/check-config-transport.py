#!/usr/bin/env python3
"""Strict host checks for the configuration envelope, CGI and private IPC."""
from pathlib import Path
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="wr-config-transport-") as directory:
    for name, extra in [("control-record", []), ("config-mailbox", ["control-mailbox.c"]), ("http-handler", [])]:
        binary = Path(directory) / name
        subprocess.run(["gcc", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-O2",
                        "-fsanitize=address,undefined", "-fno-pie", "-no-pie", "-I" + str(here),
                        str(here / ("check-" + name + ".c")), *[str(here / n) for n in extra],
                        "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=15)
for name in ("check-status-channel.py", "check-config-runtime-staging.py"):
    subprocess.run([sys.executable, "-B", str(here / name)], check=True, timeout=60)
