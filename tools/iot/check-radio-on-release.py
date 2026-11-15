"""Actual ON preflight and RC receipt cleanup under the real signal fence."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-handoff.py').read_text()
ns={'__file__':str(here/'check-radio-on-handoff.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
anchor='int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request *r){*r=receipt;return 1;}'
assert anchor in body
body=body.replace(anchor,'static int radio_off_receipt_valid=1;\nint wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request*r){memset(r,0,sizeof(*r));if(!radio_off_receipt_valid)return 0;*r=receipt;return 1;}')
body=body.replace('#include "radio-stop-fence.c"','''static int fail_unmask;
static int on_mask_hook(int how,const sigset_t*set,sigset_t*old){if(how==SIG_SETMASK&&fail_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask on_mask_hook
#include "radio-stop-fence.c"
#undef sigprocmask''')
body+=r'''
#include "radio-on-release.h"
static int auth_current=1,wan_current=1,wan_submits;
int wr_iot_rc_restart_auth_process_current(const struct wr_iot_restart_service_policy*p){assert(p->enterprise);return auth_current;}
int wr_iot_rc_restart_wan_plan(int on,enum wr_iot_wan_followup*p){assert(on==1);*p=WR_WAN_FULL_RESTART;return 1;}
int wr_iot_rc_restart_wan_current(int on,enum wr_iot_wan_followup p){assert(on==1&&p==WR_WAN_FULL_RESTART);return wan_current;}
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup p){assert(p==WR_WAN_FULL_RESTART&&!depth&&!wr_iot_rc_shutdown.active&&!radio_off_receipt_valid);wan_submits++;}
#include "restart-wan-followup.c"
#include "radio-on-release.c"
#include "radio-on-prehandoff.c"
#define radio_off_receipt receipt
#ifndef WR_IOT_FIXTURE_REAL_ON_SHUTDOWN
int wr_iot_on_shutdown_closed_current(struct wr_iot_on_restore*s,const struct wr_iot_rc_quiesce*o){(void)s;(void)o;assert(0);return 0;}
#endif
#include "radio-on-release-runtime.h"
#undef radio_off_receipt
static struct wr_iot_on_restore *releasing;
static struct wr_iot_on_admission *released_admission;
static volatile sig_atomic_t shutdowns;
static void shutdown_handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!depth&&!radio_off_receipt_valid&&!wr_iot_rc_shutdown.radio_off_owned);
 assert(releasing->phase==WR_ON_RESTORE_RELEASED&&!releasing->generation.desired.password[0]&&!releasing->generation.admission);
 assert(!released_admission->profile.active&&!released_admission->profile.files.count&&!released_admission->guard&&!released_admission->busy);
 shutdowns++;
}
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 for(int fault=0;fault<2;fault++){
  struct wr_iot_on_admission a={0};struct wr_iot_on_restore restore={0};unsigned char id[16]={1};
  receipt=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};radio_off_receipt_valid=1;
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;bridge_fail=no_submit=0;
  ram_calls=mc_calls=service_calls=0;ram_fail=mc_fail=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
  assert(wr_iot_on_admission_begin(&a)&&wr_iot_on_restore_begin(&restore,&a,&desired,1,id));
  int ready=0;for(int tick=0;tick<30&&!ready;tick++)ready=wr_iot_on_restore_step(&restore);assert(ready);
  struct wr_iot_control_request request={.id="01000000000000000000000000000000",.created=10,.request=desired};
  admitted=active=1;begins=continues=0;assert(wr_iot_on_restore_handoff(&restore,&request));
  assert(wr_iot_wan_followup_capture(&restore.wan,1)&&wr_iot_on_release_current(&restore));
  auth_current=0;assert(!wr_iot_rc_radio_on_release(&restore)&&a.profile.active&&radio_off_receipt_valid);auth_current=1;
  wan_current=0;assert(!wr_iot_on_release_current(&restore));wan_current=1;
  restore.services.attempted=6;assert(!wr_iot_on_release_current(&restore));restore.services.attempted=7;
  assert(wr_iot_on_release_current(&restore)&&!continues); /* final preflight is read-only. */
  releasing=&restore;released_admission=&a;
  struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
  if(fault){
   fail_unmask=1;assert(!wr_iot_rc_radio_on_release(&restore)&&restore.phase==WR_ON_RESTORE_RELEASING&&a.profile.active&&radio_off_receipt_valid&&depth==1);
   assert(!raise(SIGTERM)&&!shutdowns);fail_unmask=0;
  }
  assert(wr_iot_rc_radio_on_release(&restore)&&restore.phase==WR_ON_RESTORE_RELEASED&&!radio_on_releasing);
  assert(!a.profile.active&&!a.profile.files.count&&!a.guard&&!a.fence.owner&&!depth&&!radio_off_receipt_valid);
  assert(!wr_iot_rc_radio_on_release(&restore)&&!wr_iot_on_release_current(&restore));
  assert(shutdowns==fault&&!restore.generation.desired.ssid[0]);
  wan_submits=0;assert(wr_iot_wan_followup_step(&restore.wan)&&wan_submits==1);assert(wr_iot_wan_followup_step(&restore.wan)&&wan_submits==1);
  assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-release-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON RC parent release actual preflight/profile/receipt/signal fence: auth/WAN/service refusal, read-only ACTIVE, failed unmask retains all, retry wipes credentials/receipt and guard before real SIGTERM; WAN once only after release; SDK/backend actors, no final DONE/runtime')
