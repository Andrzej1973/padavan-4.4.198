"""Compile and run read-only Main-DOWN/never-opened ra2 reference fixture."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-precreated-down-') as d:
 b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/'check-precreated-down-reference.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS read-only never-opened ra2 after exact Main release: stale/owned/peer/TX/epoch/receipt refusals; driver binding and physical drain separate')
