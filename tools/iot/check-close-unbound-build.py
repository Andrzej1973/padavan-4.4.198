#!/usr/bin/env python3
"""Compile actual staged CLOSE roots without a caller, as ordinary driver TU does."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='iot-close-unbound-') as td:
 for stem in ('check-driver-api-close-entry','check-driver-api-close-progress-ioctl'):
  original=(here/(stem+'.c')).read_text()
  assert original.count('int main(void)')==1
  source=Path(td)/(stem+'.c')
  source.write_text(original.split('int main(void)',1)[0]+'int main(void){return 0;}\n')
  subprocess.run(['gcc','-O2','-std=c11','-Wall','-Wextra','-Werror','-I'+str(here),str(source),'-o',str(Path(td)/stem)],check=True)
print('PASS actual unbound CLOSE roots compile with warnings-as-errors; no endpoint installed')
