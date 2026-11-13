#!/usr/bin/env python3
"""Execute the actual nested process-context fence; no hardware access."""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='iot-radio-stop-fence-') as d:
    binary=Path(d)/'check'
    subprocess.run(['gcc','-std=c11','-D_POSIX_C_SOURCE=200809L','-Wall','-Wextra','-Werror','-O2',
                    '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),
                    str(here/'check-radio-stop-fence.c'),str(here/'radio-stop-fence.c'),
                    '-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True,timeout=10)
