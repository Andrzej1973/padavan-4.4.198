from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
script=(here/'check-reopen-rollback.py').read_text()
ns={'__file__':str(here/'check-reopen-rollback.py')}
exec(compile(script.split('with tempfile.TemporaryDirectory',1)[0],'<actual rollback fixture>','exec'),ns)
s=ns['source']
s=s.replace('#include "reopen-rollback.h"','#include "rebind-rollback.h"')
a=s.index('int wr_iot_reopen_witness_current(');b=s.index('\n',a)
s=s[:a]+'''int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request *p,const unsigned char *id,struct wr_iot_driver_identity *out){assert(depth&&p->action==WR_STOP_RELEASE&&id[0]==8);*out=(struct wr_iot_driver_identity){7,2};return witness_ok;}'''+s[b:]
s=s.replace('struct wr_iot_start_admission owner={0};','struct wr_iot_rebind_start rebind={.owner=getpid(),.identity={7,2},.physical={.action=WR_STOP_RELEASE},.open_id={8}};')
s=s.replace('owner.', 'rebind.admission.').replace('&owner','&rebind.admission')
s=s.replace('struct wr_iot_open_controller open=', 'struct wr_iot_rebind_open_controller open=')
s=s.replace('rebind.admission.reopened=1;', 'rebind.admission.reopened=2;')
s='\n'.join(line for line in s.splitlines() if 'struct wr_iot_reopen_witness witness=' not in line)
s=s.replace(';witness.close_serial=rebind.admission.idle.serial;', ';')
s=s.replace('wr_iot_reopen_rollback_step(&rollback,&network,&rebind.admission,&open,&witness)', 'wr_iot_rebind_rollback_step(&rollback,&network,&rebind,&open)')
# Add explicit attempted-OPEN refusal before any resource rollback.
anchor='  witness_ok=1;\n  open.attempt.identity.adapter_epoch=1;'
s=s.replace(anchor,'''  witness_ok=1;
  open.phase=WR_REBIND_OPEN_RETAINED;
  assert(!wr_iot_rebind_rollback_step(&rollback,&network,&rebind,&open)&&bridge_index==7);
  open.phase=WR_REBIND_OPEN_IDLE;
  open.attempt.identity.adapter_epoch=1;''')
with tempfile.TemporaryDirectory(prefix='wr-rebind-rollback-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 src=Path(d)/'check.c';out=Path(d)/'check';src.write_text(s)
 units=('rebind-rollback.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(src),*[str(here/n) for n in units],'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
print('PASS rebind pre-OPEN rollback with actual snapshot restore: observation refusal, attempted OPEN/identity refusal, partial restore retry, pending shutdown held; resource adapters injected')
