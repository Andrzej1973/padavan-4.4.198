"""Private OFF consumer composed with actual physical controller/session/fence."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
code+=r'''
#include "radio-off-policy.h"
static int policy_ok,policy_reads;
int wr_iot_rc_radio_off_policy(int reload,struct wr_iot_radio_off_policy*p){
 assert(depth==1&&wr_iot_rc_shutdown.active);policy_reads++;
 if(!policy_ok)return 0;
 *p=(struct wr_iot_radio_off_policy){reload,1,1,WR_WAN_FULL_RESTART};return 1;
}
#include "radio-off-owner.c"
int main(void){
 (void)handler;
 struct wr_iot_radio_off_owner off_owner={0};
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=7};
 assert(wr_iot_radio_off_begin(&off_owner,&off));
 assert(!wr_iot_radio_off_begin(&off_owner,&off));
 assert(!wr_iot_radio_off_prepare(&off_owner,1)&&!off_owner.policy_ready);
 policy_ok=1;assert(wr_iot_radio_off_prepare(&off_owner,1)&&off_owner.policy_ready);
 int reads=policy_reads;
 assert(wr_iot_radio_off_prepare(&off_owner,1)&&policy_reads==reads);
 assert(!wr_iot_radio_off_prepare(&off_owner,0)&&policy_reads==reads);

 assert(!wr_iot_radio_off_poll(&off_owner)&&physical.owner&&!calls);
 query_status=WR_STOP_COMPLETE;
 for(unsigned i=0;i<40&&wr_iot_rc_physical_pending();i++){
  assert(!wr_iot_radio_off_poll(&off_owner));wr_iot_rc_physical_step();
 }
 assert(physical.result==1&&!depth&&!wr_iot_rc_shutdown.active&&downs==1);
 unsigned long long created=off_owner.created;
 off_owner.created++;assert(!wr_iot_radio_off_poll(&off_owner)&&physical.owner);
 off_owner.created=created;int before=calls;
 assert(wr_iot_radio_off_poll(&off_owner)==1&&!physical.owner);
 assert(off_owner.policy_ready&&off_owner.policy.reload==1&&off_owner.policy.wan==WR_WAN_FULL_RESTART);
 assert(!wr_iot_radio_off_prepare(&off_owner,1)&&policy_reads==reads);

 assert(wr_iot_radio_off_poll(&off_owner)==1&&calls==before);
 assert(wr_iot_radio_off_take(&off_owner)==1&&!off_owner.owner);
 assert(!wr_iot_radio_off_take(&off_owner));
 /* A refused preparation is claimed once and consumed as failure, not retried. */
 calls=downs=aux_calls=0;entropy_fail=1;
 assert(wr_iot_radio_off_begin(&off_owner,&off));
 assert(!wr_iot_radio_off_poll(&off_owner));wr_iot_rc_physical_step();
 assert(wr_iot_radio_off_poll(&off_owner)==-1&&!physical.owner&&!depth);
 assert(wr_iot_radio_off_take(&off_owner)==-1&&!off_owner.owner&&!calls&&!downs);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-composition-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS OFF consumer with actual physical/session/fence: pending polling, foreign identity retained, DOWN once, RELEASE consumed once, cached receipt, entropy refusal consumed without retry; backend/transport injected')
