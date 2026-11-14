from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-rebind-stage-') as d:
 out=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/'check-rebind-start.c'),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True,timeout=15)
print('PASS rebind snapshot/staging: observation drift, failed snapshot cleanup retained, single writer attempt and post-write drift; dependencies injected')
