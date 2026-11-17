from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-view-endpoint-build-') as directory:
 binary=Path(directory)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),
  *[str(here/name) for name in ('check-config-view-endpoint.c','config-view-endpoint.c','config-view-channel.c','status-endpoint.c','status-channel.c')],
  '-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
