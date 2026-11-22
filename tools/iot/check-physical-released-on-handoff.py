"""Actual physical admission/session/fence with released ON-tail boundary actor."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
code=code.replace('int wr_iot_radio_on_off_ready(void){return 0;}', 'static int tail_ready=1,handoffs;\nint wr_iot_radio_on_off_ready(void){return tail_ready;}')
code=code.replace('int wr_iot_radio_on_off_handoff(const struct wr_iot_radio_stop_fence*f){(void)f;assert(0);return 0;}', '''int wr_iot_radio_on_off_handoff(const struct wr_iot_radio_stop_fence*f){
 assert(f==&physical.fence&&f->owner==getpid()&&f->level==1&&depth==1&&
  physical.owner==getpid()&&wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_on_owned&&
  !physical.intent.restart&&!physical.intent.radio_on&&!physical.intent.reload&&!entropy_fail);
 handoffs++;wr_iot_rc_shutdown.radio_on_owned=0;return 1;
}''')
code+=r'''
int main(void){
 (void)handler;
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=1};
 struct wr_iot_rc_physical_intent stop={0},restart={1,1,1},out={0};
 wr_iot_rc_shutdown.radio_on_owned=1;
 tail_ready=0;assert(!wr_iot_rc_physical_begin_quiesce(&stop,&off)&&!physical.owner&&!handoffs);
 tail_ready=1;assert(!wr_iot_rc_physical_begin_quiesce(&restart,&off)&&!physical.owner&&!handoffs);
 assert(!wr_iot_rc_physical_begin(&stop)&&!physical.owner&&!handoffs);
 for(int fail=0;fail<2;fail++){
  guard_fail=fail==0;entropy_fail=fail==1;
  assert(wr_iot_rc_physical_begin_quiesce(&stop,&off)&&physical.owner==getpid());
  assert(wr_iot_rc_shutdown.radio_on_owned&&!handoffs&&!physical.quiesce.owner);
  wr_iot_rc_physical_step();assert(!depth&&!wr_iot_rc_shutdown.active);
  assert(wr_iot_rc_physical_take(&out)==-1&&wr_iot_rc_shutdown.radio_on_owned&&!calls&&!downs);
 }
 guard_fail=entropy_fail=0;
 assert(wr_iot_rc_physical_begin_quiesce(&stop,&off)&&handoffs==1&&!wr_iot_rc_shutdown.radio_on_owned);
 assert(physical.owner==getpid()&&physical.quiesce.owner==getpid()&&depth==1&&wr_iot_rc_shutdown.active);
 query_status=WR_STOP_COMPLETE;
 for(int i=0;i<40&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(!wr_iot_rc_physical_pending()&&!depth&&!wr_iot_rc_shutdown.active&&downs==1&&handoffs==1);
 assert(wr_iot_rc_physical_take(&out)==1&&!out.restart&&!out.radio_on);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-physical-on-tail-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual physical OFF admission: tail readiness, restart/native refusal, guard/entropy failures preserve ON actor; handoff only under physical fence/guard, real session through RELEASE, one DOWN; backend/ON boundary actors')
