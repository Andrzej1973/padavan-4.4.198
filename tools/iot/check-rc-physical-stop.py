"""Native composition of retained RC admission, actual session and signal fence."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-rc-physical-') as d:
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),
  str(here/'check-rc-physical-stop.c'),str(here/'physical-stop-session.c'),
  str(here/'radio-stop-fence.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual retained RC admission/session/fence: intent copied, preparation refusal balanced, guards held across uncertainty, DOWN once, deferred SIGTERM after cleanup; backend/transport hooks injected')
