"""Drain routed shutdown after actual INITIAL scheduler/WAN/IAPP cancellation."""
from pathlib import Path
root=Path(__file__).resolve().parent
text=(root/'check-physical-scheduler-unmask-boundary.py').read_text()
extra=r'''
# Put the real normal controller beside physical state. Existing TU namespacing
# keeps private state private; explicit wrappers bind backend publication to it.
for name in ['wr_iot_rc_backend_closed','wr_iot_rc_quiesce_begin','wr_iot_rc_quiesce_shutdown_begin','wr_iot_rc_quiesce_advance','wr_iot_rc_boot_idle']:
 if re.search(r'^(?:static )?(?:int|void) '+re.escape(name)+r'\(',physical,re.M):physical=remove_function(physical,name)
physical=physical.replace('static int quiesce_steps;','').replace('guard_fail,closed_fail,','guard_fail,')
physical=physical.replace('r->epoch==11&&r->generation==12&&r->open_token==13&&r->closed_serial==14&&r->nonce[0]==7','r->epoch==2&&r->generation==2&&r->open_token==3&&r->closed_serial>0')
physical+=r"""
#include "rc-normal-shutdown.c"
void normal_fixture_prepare(void){
 assert(!physical.owner&&!depth&&!wr_iot_rc_shutdown.active&&downs==1&&initial_calls==3);
 calls=downs=aux_calls=initial_calls=0;query_status=WR_STOP_COMPLETE;
}
int normal_fixture_done(void){
 if(!normal_shutdown.spent)return 0;
 assert(!physical.owner&&!depth&&!wr_iot_rc_shutdown.active&&downs==1&&calls==3&&aux_calls==6);
 return 1;
}
"""
for name in ['wr_iot_rc_normal_shutdown_arm_ready','wr_iot_rc_normal_shutdown_arm_commit']:backend=remove_function(backend,name)
backend=r"""
int physical_fixture_wr_iot_rc_normal_shutdown_arm_ready(void);
void physical_fixture_wr_iot_rc_normal_shutdown_arm_commit(void);
int physical_fixture_wr_iot_rc_normal_shutdown_step(void);
int physical_fixture_wr_iot_rc_normal_shutdown_pending(void);
void physical_fixture_normal_fixture_prepare(void);
int physical_fixture_normal_fixture_done(void);
int wr_iot_rc_normal_shutdown_arm_ready(void){return physical_fixture_wr_iot_rc_normal_shutdown_arm_ready();}
void wr_iot_rc_normal_shutdown_arm_commit(void){physical_fixture_wr_iot_rc_normal_shutdown_arm_commit();}
"""+backend
a='assert(!memcmp(&pump,&empty,sizeof(pump))&&!memcmp(&kept,&backend,sizeof(backend)));return 0;'
assert a in backend
backend=backend.replace(a,a[:-len('return 0;')]+r"""
 if(wr_iot_rc_shutdown.normal_route_requested){
  assert(wr_iot_restart_scheduler_unowned()&&!wr_iot_restart_scheduler_pending());
  assert(backend.phase==WR_IOT_OWNER_OFF&&!backend.start.input.request.password[0]&&!physical_replays);
  physical_fixture_normal_fixture_prepare();
  for(unsigned n=0;n<150&&!physical_fixture_normal_fixture_done();n++)physical_fixture_wr_iot_rc_normal_shutdown_step();
  assert(physical_fixture_normal_fixture_done()&&physical_replays==1);
  assert(!physical_fixture_wr_iot_rc_normal_shutdown_pending());
  assert(backend.phase==WR_IOT_OWNER_OFF&&!backend.start.input.request.password[0]);
 }
"""+'return 0;',1)
'''
needle='needle="text=text.replace(marker,'
i=text.index(needle)
text=text[:i]+'extra+='+repr(extra)+'\n'+text[i:]
exec(compile(text,__file__,'exec'),{'__file__':__file__})
print('PASS actual INITIAL scheduler/WAN/IAPP shutdown: cancellation retains routed TERM, real normal consumer drains same OFF backend through physical RELEASE and one stock replay; driver/network actors, no device proof')
