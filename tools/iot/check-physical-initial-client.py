"""Host WPIQ client/session: syscall faults, exact correlation and one DOWN."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-initial-client-session-') as d:
 for name in ('client','session'):
  command=['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/('check-physical-initial-'+name+'.c'))]
  if name=='session':command.append(str(here/'physical-initial-session.c'))
  subprocess.run(command+['-o',d+'/'+name],check=True)
  subprocess.run([d+'/'+name],check=True,timeout=15)
print('PASS distinct WPIQ client/session: exact nonce/attempt, uncertain calls retain phase, one DOWN, no replay after possible submission, CANCEL/RELEASE terminal retries, foreign/reentrant refusal; syscalls/kernel mocked, RC integration pending')
