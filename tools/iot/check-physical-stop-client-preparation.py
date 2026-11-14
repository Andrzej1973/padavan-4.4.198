"""Actual runtime preparer links isolated client objects without RC activation."""
from pathlib import Path
import json,subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-stop-client-prepared-') as d:
 root=Path(d);rc=root/'trunk/user/rc';http=root/'trunk/user/httpd'
 for role in (rc,http):(role/'wr-iot').mkdir(parents=True)
 (root/'iot-control-source.json').write_text(json.dumps({'board':'WR1200JS'}))
 (rc/'wr-iot/activation-owner.h').write_text('/* prerequisite marker only */')
 (rc/'init.c').write_text('#include "wr-iot/rc-shutdown-admission.h"\n\t\t\t\tsigsuspend(&ss);\n')
 (rc/'Makefile').write_text('OBJS += wr-iot-control-mailbox.o wr-iot-control-server.o\n')
 (http/'Makefile').write_text('OBJS += wr-iot-control-mailbox.o wr-iot-control-client.o\n')
 (rc/'wr-iot/driver-api-wire.h').write_bytes((here/'driver-api-wire.h').read_bytes())
 subprocess.run(['python3',str(here/'prepare-runtime.py'),str(root)],check=True)
 manifest=json.loads((root/'iot-runtime-source.json').read_text())
 assert manifest['physical_stop_transport_linked'] and not manifest['physical_stop_rc_orchestration']
 for name in ('physical-stop-client','physical-stop-down','physical-stop-session'):
  assert (rc/'Makefile').read_text().count('wr-iot-'+name+'.o')==1
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-I'+str(rc),'-c',str(rc/('wr-iot-'+name+'.c')),'-o',str(root/(name+'.o'))],check=True)
 duplicate=subprocess.run(['python3',str(here/'prepare-runtime.py'),str(root)],capture_output=True)
 assert duplicate.returncode!=0
print('PASS actual runtime preparation: fixed client/DOWN objects copied and compile, exact Makefile entries, no orchestration flag, duplicate refused; full SDK/MIPS separate')
