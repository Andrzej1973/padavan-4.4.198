#!/usr/bin/env python3
"""Execute configuration parser tests against the installed candidate header."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='wr-config-result-') as td:
 c=Path(td)/'check.c';c.write_text(Path(__file__).with_suffix('.c').read_text())
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate.resolve()/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
