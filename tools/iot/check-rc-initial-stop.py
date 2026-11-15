"""Actual initial RC subcontroller/session with external effects injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-rc-initial-stop-') as d:
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/'check-rc-initial-stop.c'),str(here/'rc-initial-stop.c'),str(here/'physical-initial-session.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS RC initial auth/AUX/fresh ARM/session: foreign and pending refusal, failed observation retained, uncertain ARM, one possible DOWN, COMPLETE/RELEASE or unsubmitted-DOWN/CANCEL, typed terminal no replay; outer owner/device integration pending')
