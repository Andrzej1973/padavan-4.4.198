"""Actual rebind network sequencer/matcher, external resources/readback injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
script=(here/'check-start-network-composition.py').read_text()
scope={'__file__':str(here/'check-start-network-composition.py')}
exec(compile(script.split('with tempfile.TemporaryDirectory',1)[0],'<existing resource fixture>','exec'),scope)
source=scope['source']
source=source.replace('#include "start-network.c"',r'''
#include "rebind-network.h"
static int observation_ok=1,observed,drift_after_operation;
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request *p,const unsigned char *id,struct wr_iot_driver_identity *out){assert(p->action==WR_STOP_RELEASE&&id[0]==8);observed++;*out=(struct wr_iot_driver_identity){7+(unsigned)(drift_after_operation&&operations),2};return observation_ok;}
#include "rebind-network.c"
''')
source=source.replace('struct wr_iot_start_admission owner={0};', 'struct wr_iot_rebind_start rebind={.owner=getpid(),.identity={7,2},.physical={.action=WR_STOP_RELEASE},.open_id={8}};struct wr_iot_start_admission *owner=&rebind.admission;')
source=source.replace('owner.', 'owner->')
source=source.replace('owner->admitted=owner->mutation_started=', 'owner->reopened=2;owner->admitted=owner->mutation_started=')
source=source.replace('unsigned char nonce[16]={1};', '')
source=source.replace('wr_iot_start_network_step(&state,&owner,&request,nonce)', 'wr_iot_rebind_network_step(&state,&rebind,&request)')
anchor='  serial=1;operations=bridge='
source=source.replace(anchor,'''  int saved_fail=fail;fail=0;operations=bridge=quarantine=attached=up=network=dns=policy=0;observation_ok=0;wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  assert(!wr_iot_rebind_network_step(&state,&rebind,&request)&&state.phase==WR_IOT_NET_RECOVERY&&!operations);
  observation_ok=1;state=(struct wr_iot_start_network){0};
  drift_after_operation=1;
  assert(!wr_iot_rebind_network_step(&state,&rebind,&request)&&state.phase==WR_IOT_NET_RECOVERY&&operations==1&&state.attempted==1);
  drift_after_operation=0;state=(struct wr_iot_start_network){0};fail=saved_fail;
'''+anchor)
source=source.replace('PASS actual network sequencer plus installed matcher/gate writer:', 'PASS actual physical-rebind network sequencer/matcher:')
with tempfile.TemporaryDirectory(prefix='wr-rebind-network-') as d:
 src=Path(d)/'check.c';out=Path(d)/'check';src.write_text(source)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
