"""Actual RC release -> WAN -> post-network -> terminal IAPP progression."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-release.py').read_text()
ns={'__file__':str(here/'check-radio-on-release.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "radio-on-followup.h"
static int network_current=1,led_calls,child_begins,child_steps,child_failure,child_unknown;
int wr_iot_rc_backend_observed(const struct wr_iot_control_result*r){assert(r->created==10&&!strcmp(r->id,"01000000000000000000000000000000")&&r->state==WR_IOT_RESULT_APPLIED);return network_current;}
int wr_iot_rc_restart_led_on(void){assert(!depth&&!wr_iot_rc_shutdown.active&&wan_submits==1);led_calls++;return 1;}
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*c){assert(depth==1&&!c->owner);child_begins++;c->owner=getpid();c->attempted=1;c->fd=77;return 1;}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*c){assert(depth==1&&c->owner==getpid());child_steps++;if(child_unknown)return -2;c->fd=-1;c->result=child_failure?-1:1;return c->result;}
#include "restart-terminal-iapp.c"
#include "radio-on-followup.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int fault=0;fault<3;fault++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_restore restore={0};unsigned char id[16]={1};
  receipt=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};radio_off_receipt_valid=1;
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;bridge_fail=no_submit=0;
  ram_calls=mc_calls=service_calls=0;ram_fail=mc_fail=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
  auth_current=wan_current=1;wan_submits=led_calls=child_begins=child_steps=0;network_current=1;child_failure=fault==1;child_unknown=fault==2;
  releasing=&restore;released_admission=&a;
  struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
  assert(wr_iot_on_admission_begin(&a)&&wr_iot_on_restore_begin(&restore,&a,&desired,1,id));
  int ready=0;for(int tick=0;tick<30&&!ready;tick++)ready=wr_iot_on_restore_step(&restore);assert(ready);
  struct wr_iot_control_request request={.id="01000000000000000000000000000000",.created=10,.request=desired};
  admitted=active=1;begins=continues=0;assert(wr_iot_on_restore_handoff(&restore,&request));
  assert(wr_iot_rc_radio_on_release(&restore)&&!depth&&!radio_off_receipt_valid);
  assert(!wr_iot_on_followup_step(&restore)&&restore.phase==WR_ON_RESTORE_WAN&&!wan_submits);
  network_current=0;assert(!wr_iot_on_followup_step(&restore)&&wan_submits==1&&!led_calls&&!child_begins);
  assert(!wr_iot_on_followup_step(&restore)&&wan_submits==1);network_current=1;
  assert(!wr_iot_on_followup_step(&restore)&&led_calls==1&&restore.phase==WR_ON_RESTORE_IAPP_PENDING);
  assert(!wr_iot_on_followup_step(&restore));
#if WR_IOT_IAPP_POLICY_PREPARED
  assert(restore.phase==WR_ON_RESTORE_IAPP&&depth==1&&wr_iot_rc_shutdown.active);
  assert(!wr_iot_on_followup_step(&restore)&&child_begins==1);
  if(child_unknown){for(int i=0;i<3;i++)assert(!wr_iot_on_followup_step(&restore)&&depth==1&&child_begins==1);child_unknown=0;}
  int result=wr_iot_on_followup_step(&restore);
  assert(result==!child_failure&&!depth&&!wr_iot_rc_shutdown.active&&child_begins==1);
  assert(restore.phase==(child_failure?WR_ON_RESTORE_RETAINED:WR_ON_RESTORE_DONE));
  if(!child_failure){assert(wr_iot_on_followup_step(&restore));network_current=0;assert(!wr_iot_on_followup_step(&restore));network_current=1;}
#else
  assert(restore.phase==WR_ON_RESTORE_IAPP_PENDING&&!child_begins&&!depth);
#endif
  assert(wan_submits==1&&led_calls==1&&ups==1&&generator_calls==1&&!a.profile.active);
  assert(!unlink(profile_path));
 }
}
'''
for gate in (0,1):
    with tempfile.TemporaryDirectory(prefix='wr-on-followup-') as d:
        root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
        prefix=f'#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED {gate}\n'
        p=root/'check.c';p.write_text(prefix+body);b=root/'check'
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
        subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON actual release/WAN/terminal fence composition: WAN once after release, lost post-WAN proof holds LED/IAPP, LED once, default gate inert, paired IAPP one child/unknown drains/success DONE/failure retained; backend and SDK child actors, no physical acceptance')
