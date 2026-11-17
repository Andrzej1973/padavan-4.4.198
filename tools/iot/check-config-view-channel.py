from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-view-protocol-') as directory:
 binary=Path(directory)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),
  str(here/'config-view-channel.c'),str(here/'check-config-view-channel.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=25)
