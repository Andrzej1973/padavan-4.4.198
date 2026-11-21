#!/usr/bin/env python3
"""Actual reopen sequencer + actual request matcher; resource/witness queries injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
# Reuse the initial-network composition generator's exact resource/matcher
# fixture setup, then replace only admission observation and entry point.
script=(here/'check-start-network-composition.py').read_text()
prefix=script.split('with tempfile.TemporaryDirectory',1)[0]
scope={'__file__':str(here/'check-start-network-composition.py')}
exec(compile(prefix,'initial-network-fixture','exec'),scope)
source=scope['source']
source=source.replace('#include "start-network.c"',r'''
#include "reopen-network.h"
static int witness_ok=1;
int wr_iot_reopen_witness_current(const struct wr_iot_reopen_witness *w){assert(w&&w->owner==getpid()&&w->valid);return witness_ok;}
#include "reopen-network.c"
''')
source=source.replace('owner.admitted=owner.mutation_started=', 'owner.reopened=1;owner.admitted=owner.mutation_started=')
source=source.replace('unsigned char nonce[16]={1};','struct wr_iot_reopen_witness witness={.owner=getpid(),.valid=1,.attempt={.identity={1,2}},.close_serial=1};')
source=source.replace('wr_iot_start_network_step(&state,&owner,&request,nonce)','wr_iot_reopen_network_step(&state,&owner,&request,&witness)')
anchor='  serial=1;operations=bridge='
source=source.replace(anchor,'  serial=1;operations=bridge=quarantine=attached=up=network=dns=policy=0;\n  witness_ok=0;wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;\n  assert(!wr_iot_reopen_network_step(&state,&owner,&request,&witness)&&state.phase==WR_IOT_NET_RECOVERY&&!operations);\n  witness_ok=1;state=(struct wr_iot_start_network){0};\n'+anchor)
source=source.replace('  assert(ready==(fail==0));','  assert(serial==1);\n  assert(ready==(fail==0));')
source=source.replace('PASS actual network sequencer plus installed matcher/gate writer:', 'PASS actual reopen network sequencer plus installed matcher/gate writer:')
with tempfile.TemporaryDirectory(prefix='iot-reopen-network-') as d:
 unit=Path(d)/'check.c';unit.write_text(source);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
