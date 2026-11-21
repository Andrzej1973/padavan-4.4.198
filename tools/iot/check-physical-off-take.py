"""Exact private OFF-envelope terminal consumer; no SDK or hardware acceptance."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
code+=r'''
int main(void){
 (void)handler;
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=7};
 struct wr_iot_rc_physical_intent stop={0};
 assert(wr_iot_rc_physical_begin_quiesce(&stop,&off));
 assert(!wr_iot_rc_physical_take_off(off.id,off.created));
 query_status=WR_STOP_COMPLETE;
 for(unsigned i=0;i<40&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(physical.result==1&&!depth&&!wr_iot_rc_shutdown.active);
 struct wr_iot_physical_stop_request released={0};
 assert(!wr_iot_rc_physical_off_read(off.id,8,&released)&&!released.epoch);
 physical.session.busy=1;assert(!wr_iot_rc_physical_off_read(off.id,7,&released));physical.session.busy=0;
 assert(wr_iot_rc_physical_off_read(off.id,7,&released));
 assert(released.action==WR_STOP_RELEASE&&released.epoch==11&&released.generation==12&&released.attempt==19);
 physical.quiesce.active=1;assert(!wr_iot_rc_physical_off_read(off.id,7,&released)&&!released.epoch);physical.quiesce.active=0;

 assert(!wr_iot_rc_physical_take_off(NULL,7));
 assert(!wr_iot_rc_physical_take_off("short",7));
 assert(!wr_iot_rc_physical_take_off(off.id,8));
 assert(!wr_iot_rc_physical_take_off("22222222222222222222222222222222",7));
 physical.intent.restart=1;assert(!wr_iot_rc_physical_take_off(off.id,7));physical.intent.restart=0;
 pid_t owner=physical.owner;physical.owner++;assert(!wr_iot_rc_physical_take_off(off.id,7));physical.owner=owner;
 int before=calls;
 assert(wr_iot_rc_physical_take_off(off.id,7)==1&&!physical.owner);
 assert(!wr_iot_rc_physical_take_off(off.id,7)&&calls==before);
 assert(!wr_iot_rc_physical_off_read(off.id,7,&released)&&!released.epoch);
 calls=downs=aux_calls=0;closed_fail=1;
 assert(wr_iot_rc_physical_begin_quiesce(&stop,&off));
 /* Explicit preparation failure still belongs to its original OFF envelope. */
 physical.finishing=-1;wr_iot_rc_physical_step();
 assert(wr_iot_rc_physical_take_off(off.id,7)==-1&&!physical.owner&&!depth);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-take-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS private OFF take: pending/foreign/restart/malformed refuse, exact success/failure consumed once, no driver replay; transport injected')
