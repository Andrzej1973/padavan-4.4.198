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
 assert(!wr_iot_radio_off_step(&off_owner,1)&&!off_owner.policy_ready&&!aux_calls&&!calls&&!downs);
 policy_ok=1;assert(wr_iot_radio_off_prepare(&off_owner,1)&&off_owner.policy_ready);
 int reads=policy_reads;
 assert(wr_iot_radio_off_prepare(&off_owner,1)&&policy_reads==reads);
 assert(!wr_iot_radio_off_prepare(&off_owner,0)&&policy_reads==reads);

 assert(!wr_iot_radio_off_poll(&off_owner)&&physical.owner&&!calls);
 query_status=WR_STOP_COMPLETE;
 for(unsigned i=0;i<40&&wr_iot_rc_physical_pending();i++){
  assert(!wr_iot_radio_off_poll(&off_owner));
  if(physical.session.phase==WR_PHYSICAL_SESSION_RELEASE)wr_iot_rc_physical_step();
  else (void)wr_iot_radio_off_step(&off_owner,1);
 }
 assert(physical.result==1&&!depth&&!wr_iot_rc_shutdown.active&&downs==1);
 unsigned long long created=off_owner.created;
 off_owner.created++;assert(!wr_iot_radio_off_poll(&off_owner)&&physical.owner);
 off_owner.created=created;int before=calls;
 assert(wr_iot_radio_off_poll(&off_owner)==1&&!physical.owner);
 assert(off_owner.released.action==WR_STOP_RELEASE&&off_owner.released.epoch==11&&off_owner.released.attempt==19);
 assert(off_owner.policy_ready&&off_owner.policy.reload==1&&off_owner.policy.wan==WR_WAN_FULL_RESTART);
 assert(!wr_iot_radio_off_prepare(&off_owner,1)&&policy_reads==reads);

 assert(wr_iot_radio_off_poll(&off_owner)==1&&calls==before);
 assert(wr_iot_radio_off_take(&off_owner)==1&&!off_owner.owner);
 assert(!wr_iot_radio_off_take(&off_owner));
 /* Complete a second transaction through the new progress API alone. */
 calls=downs=aux_calls=quiesce_steps=0;
 assert(wr_iot_radio_off_begin(&off_owner,&off));
 assert(!wr_iot_radio_off_step(&off_owner,2)&&!calls&&!aux_calls);
 for(unsigned i=0;i<40&&!off_owner.result;i++)(void)wr_iot_radio_off_step(&off_owner,0);
 assert(off_owner.result==1&&!physical.owner&&downs==1&&!depth);
 int once=calls;assert(wr_iot_radio_off_step(&off_owner,0)==1&&calls==once);
 assert(wr_iot_radio_off_take(&off_owner)==1);
 /* A refused preparation is claimed once and consumed as failure, not retried. */
 calls=downs=aux_calls=0;entropy_fail=1;
 assert(wr_iot_radio_off_begin(&off_owner,&off));
 assert(!wr_iot_radio_off_poll(&off_owner));
 assert(wr_iot_rc_physical_off_failed(off.id,off.created));
 assert(!wr_iot_rc_physical_off_failed(off.id,off.created+1));
 policy_ok=0;assert(wr_iot_radio_off_step(&off_owner,0)==-1);
 assert(wr_iot_radio_off_poll(&off_owner)==-1&&!physical.owner&&!depth);
 assert(wr_iot_radio_off_take(&off_owner)==-1&&!off_owner.owner&&!calls&&!downs);
}
'''
prepared_code=code.replace('#define _GNU_SOURCE','#define _GNU_SOURCE\n#include <stdio.h>\n#include <fcntl.h>\nstatic char history_path[1024];static int history_capture=1;',1)
anchor=' q->owner=getpid();q->active=q->resume_needed=1;'
assert prepared_code.count(anchor)==1
prepared_code=prepared_code.replace(anchor,r'''
 if(history_capture){
  q->profile_binding.kind=WR_PROFILE_BACKEND_ACTIVE;
  strcpy(q->profile_binding.id,"01000000000000000000000000000000");q->profile_binding.created=1;
  q->profile_binding.identity=(struct wr_iot_driver_identity){11,12};
  q->profile_receipt.owner=getpid();q->profile_receipt.valid=1;
  assert(strlen(history_path)<sizeof(q->profile_receipt.path));strcpy(q->profile_receipt.path,history_path);
  assert(wr_iot_generated_capture(&q->profile_receipt.file,history_path));
 }
'''+anchor)
anchor='int main(void){'
assert prepared_code.count(anchor)==1
prepared_code=prepared_code.replace(anchor,r'''
int wr_iot_service_guard_dup(void){return depth?open("/dev/null",O_RDONLY|O_CLOEXEC):-1;}
int main(int argc,char**argv){
 assert(argc==2&&strlen(argv[1])<sizeof(history_path));strcpy(history_path,argv[1]);
 FILE*f=fopen(history_path,"w");assert(f&&fputs("historical profile A\n",f)>=0&&!fclose(f));
''')
anchor=' unsigned long long created=off_owner.created;'
assert prepared_code.count(anchor)==1
prepared_code=prepared_code.replace(anchor,r'''
 struct wr_iot_physical_stop_request expected={0};struct wr_iot_profile_binding binding={0};struct wr_iot_restart_profile_receipt proof={0};
 assert(wr_iot_rc_physical_off_read(off.id,off.created,&expected));
 expected.nonce[0]++;assert(!wr_iot_rc_physical_off_profile(off.id,off.created,&expected,&binding,&proof)&&!proof.valid&&!binding.kind);expected.nonce[0]--;
 expected.attempt++;assert(!wr_iot_rc_physical_off_profile(off.id,off.created,&expected,&binding,&proof));expected.attempt--;
 assert(!wr_iot_rc_physical_off_profile(off.id,off.created+1,&expected,&binding,&proof));
 physical.quiesce.profile_binding.identity.adapter_epoch++;assert(!wr_iot_rc_physical_off_profile(off.id,off.created,&expected,&binding,&proof));physical.quiesce.profile_binding.identity.adapter_epoch--;
 assert(wr_iot_rc_physical_off_profile(off.id,off.created,&expected,&binding,&proof)&&proof.valid&&binding.created==1);
'''+anchor)
anchor=' assert(off_owner.released.action==WR_STOP_RELEASE&&off_owner.released.epoch==11&&off_owner.released.attempt==19);'
assert prepared_code.count(anchor)==1
prepared_code=prepared_code.replace(anchor,anchor+r'''
 assert(off_owner.profile_receipt.valid&&off_owner.profile_binding.identity.adapter_epoch==11);
 assert(!strcmp(off_owner.profile_binding.id,"01000000000000000000000000000000"));
 assert(!wr_iot_rc_physical_off_profile(off.id,off.created,&expected,&binding,&proof)&&!proof.valid); /* Physical owner consumed. */
''')
anchor=' assert(wr_iot_radio_off_take(&off_owner)==-1&&!off_owner.owner&&!calls&&!downs);'
assert prepared_code.count(anchor)==1
prepared_code=prepared_code.replace(anchor,anchor+r'''
 /* Absent/changed history never prevents existing physical OFF completion,
  * but no metadata can be handed to its later no-reload profile consumer. */
 for(int fault=0;fault<2;fault++){
  calls=downs=aux_calls=quiesce_steps=0;entropy_fail=0;policy_ok=1;history_capture=fault;
  assert(wr_iot_radio_off_begin(&off_owner,&off));
  for(unsigned i=0;i<40&&wr_iot_rc_physical_pending();i++){
   if(physical.session.phase==WR_PHYSICAL_SESSION_RELEASE)wr_iot_rc_physical_step();
   else (void)wr_iot_radio_off_step(&off_owner,0);
  }
  assert(physical.result==1&&!depth);
  if(fault){FILE*f=fopen(history_path,"a");assert(f&&fputs("# foreign drift\n",f)>=0&&!fclose(f));}
  assert(wr_iot_radio_off_poll(&off_owner)==1&&!physical.owner&&!off_owner.profile_receipt.valid);
  assert(!off_owner.profile_binding.kind&&wr_iot_radio_off_take(&off_owner)==1);
 }
 assert(!unlink(history_path));
''')

with tempfile.TemporaryDirectory(prefix='wr-off-composition-') as d:
 p=Path(d)/'check.c';b=Path(d)/'check'
 for prepared,source in [(0,code),(1,prepared_code)]:
  p.write_text(source)
  subprocess.run(['gcc','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED='+str(prepared),'-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
  subprocess.run([str(b),str(Path(d)/'profile')],check=True,timeout=15)
print('PASS OFF consumer with actual physical/session/fence: pending polling, foreign identity retained, DOWN once, RELEASE consumed once, cached receipt, entropy refusal consumed without retry; backend/transport injected')
