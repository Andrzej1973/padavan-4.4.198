"""Actual INITIAL parent cleanup followed by normal physical shutdown."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'check-physical-parent-backend-composed.py').read_text()
cut=source.index('\nwith tempfile.TemporaryDirectory(')
exec(compile(source[:cut],'<initial physical composition>','exec'))
# Physical TU must use the same real backend/normal-OFF functions, not actors.
for name in ['wr_iot_rc_backend_closed','wr_iot_rc_quiesce_begin','wr_iot_rc_quiesce_shutdown_begin','wr_iot_rc_quiesce_advance','wr_iot_rc_boot_idle']:
 if re.search(r'^(?:static )?(?:int|void) '+re.escape(name)+r'\(',physical,re.M):physical=remove_function(physical,name)
physical=physical.replace('static int quiesce_steps;','').replace('guard_fail,closed_fail,','guard_fail,')
physical=physical.replace('r->epoch==11&&r->generation==12&&r->open_token==13&&r->closed_serial==14&&r->nonce[0]==7','r->epoch==2&&r->generation==2&&r->open_token==3&&r->closed_serial>0')
physical+=r'''
void physical_fixture_shutdown_prepare(void){
 assert(!physical.owner&&!depth&&!wr_iot_rc_shutdown.active&&downs==1&&initial_calls==3);
 calls=downs=aux_calls=initial_calls=0;query_status=WR_STOP_COMPLETE;
}
void physical_fixture_shutdown_done(void){
 assert(!physical.owner&&!depth&&!wr_iot_rc_shutdown.active&&downs==1&&calls==3&&aux_calls==6);
}
'''
backend=backend.replace('static volatile sig_atomic_t physical_replays;', 'static int expected_normal_off;static volatile sig_atomic_t physical_replays;').replace('physical_replays++;', 'if(expected_normal_off)assert(backend.phase==WR_IOT_OWNER_OFF&&!backend.start.input.request.password[0]);physical_replays++;')
backend=backend.replace('int main(int argc,char **argv){','#include "rc-normal-shutdown.c"\nvoid physical_fixture_shutdown_prepare(void);void physical_fixture_shutdown_done(void);\nint main(int argc,char **argv){',1)
a=' physical_fixture_terminal();assert(wr_iot_rc_initial_restart_postrelease_current(&receipt));'
assert a in backend
backend=backend.replace(a,a+r'''
 physical_fixture_shutdown_prepare();
 close_result=progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 expected_normal_off=1;assert(wr_iot_rc_shutdown_route_arm()&&!raise(SIGTERM)&&!physical_replays);
 for(unsigned i=0;i<150&&!normal_shutdown.spent;i++)wr_iot_rc_normal_shutdown_step();
 assert(normal_shutdown.spent&&physical_replays==1&&backend.phase==WR_IOT_OWNER_OFF);
 assert(!backend.start.input.request.password[0]&&!wr_iot_rc_normal_shutdown_pending());
 physical_fixture_shutdown_done();
''',1)
tail=source[cut:]
a=" physical_public={'wr_iot_physical_stop_call'"
assert a in tail
tail=tail.replace(a," physical_public={'physical_fixture_shutdown_prepare','physical_fixture_shutdown_done','wr_iot_rc_physical_begin_routed_shutdown','wr_iot_rc_physical_pending','wr_iot_rc_physical_step','wr_iot_rc_physical_off_failed','wr_iot_rc_physical_shutdown_release_cleanup', 'wr_iot_physical_stop_call'",1)
# Focus this fixture on successful INITIAL finish followed by normal shutdown.
a=tail.index(' import os\n');b=tail.index("print('PASS actual physical INITIAL",a)
tail=tail[:a]+tail[b:]
exec(compile(tail,__file__,'exec'))
print('PASS INITIAL parent cleanup then actual normal shutdown controller/backend/OFF/physical RELEASE: exact ownership and credentials retired before one TERM; explicit arming and hardware/network actors')
