"""Actual physical/fence cancellation without an invented OFF context."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rc-resume-cancel.py').read_text();ns={'__file__':str(here/'check-rc-resume-cancel.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<cancel fixture>','exec'),ns)
code=ns['code'].replace('assert(s&&q);return proof_ok;', 'assert(s&&!q);return proof_ok;')
code=code.replace('struct wr_iot_rc_quiesce off_context={0};','').replace('wr_iot_rc_physical_resume_cancel(&root,&off_context)','wr_iot_rc_physical_resume_cancel(&root,NULL)')
with tempfile.TemporaryDirectory(prefix='wr-preopen-physical-cancel-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual physical pre-OPEN cancellation: no OFF context, failed proof/mask retains state, cleanup before real queued SIGTERM, terminal cancellation once; rejected-state gate and driver actors injected')
