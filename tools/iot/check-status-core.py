#!/usr/bin/env python3
"""Run ABI status extraction under strict C11 before publishing changes."""
from pathlib import Path
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="wr-iot-status-core-") as directory:
 root=Path(directory);source=root/"status.c";binary=root/"check"
 subprocess.run([sys.executable,"-B",str(here/"prepare-status-check.py"),str(here/"control-client.c"),str(source)],check=True)
 subprocess.run(["gcc","-std=c11","-Wall","-Wextra","-Werror","-O2","-fsanitize=address,undefined","-fno-pie","-no-pie",str(source),"-o",str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
