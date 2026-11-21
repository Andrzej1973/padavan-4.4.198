"""Actual cold parent/profile/Guest/service orchestration; SDK boundaries injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-cold-on-guest.py').read_text()
ns={'__file__':str(here/'check-cold-on-guest.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
body=body.replace('static unsigned char nonce[16]={1};','')
body=body.replace('static int service_calls;', 'static int service_calls,service_fail;').replace('service_calls++;return WR_SERVICE_RETURNED;', 'service_calls++;return service_fail?WR_SERVICE_UNCERTAIN:WR_SERVICE_RETURNED;')
body+=r'''
#include "cold-on-multicast.h"
static int mc_calls,mc_fail;
int wr_iot_rc_restart_multicast_policy(struct wr_iot_multicast_policy*p){*p=(struct wr_iot_multicast_policy){1,1,guest_desired};return 1;}
int wr_iot_restart_multicast_apply(unsigned b,int e){assert(b<2&&e==1);mc_calls++;return !mc_fail;}
int wr_iot_restart_multicast_current(unsigned b,int e){assert(b<2&&e==1);return !mc_fail;}
#include "cold-on-multicast.c"
#include "precreated-down-recovery.c"
#include "cold-on-recovery.c"
#include "cold-on-owner.c"

#include "initial-off.c"
#include "cold-on-disabled.c"
static int auth=1,aux=1,wan_policy=1,wan_captures,disabled_plan,wan_submits;
int wr_iot_on_aux_down_current(void){return aux;}
int wr_iot_rc_restart_auth_process_current(const struct wr_iot_restart_service_policy*p){assert(p->enterprise==1);return auth;}
#include "cold-on-policy.c"
#include "restart-wan-followup.h"
int wr_iot_rc_restart_wan_plan(int radio,enum wr_iot_wan_followup*out){assert(radio==1);wan_captures++;*out=(enum wr_iot_wan_followup)disabled_plan;return 1;}
int wr_iot_rc_restart_wan_current(int radio,enum wr_iot_wan_followup plan){assert(radio==1&&plan==(enum wr_iot_wan_followup)disabled_plan);return wan_policy;}
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup plan){assert(plan==(enum wr_iot_wan_followup)disabled_plan);wan_submits++;auth=0;}
#include "restart-wan-followup.c"
#include "cold-on-disabled-release.c"
#include "activation-owner.h"
static struct wr_iot_activation_owner backend;
static struct {pid_t owner;} rebind;
static const struct wr_iot_cold_owner *wr_iot_cold_backend_parent;
#include "rc-cold-disabled-release.inc"
#include "rc-cold-disabled-followup.inc"
#include "restart-terminal-iapp.h"
static int led_calls,child_calls,child_outcome,led_failure;
int wr_iot_rc_restart_led_on(void){led_calls++;return !led_failure;}
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*s){assert(!s->owner);child_calls++;s->owner=getpid();s->attempted=1;s->fd=9;return 1;}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){if(!child_outcome)return -2;s->fd=-1;s->result=child_outcome;return child_outcome;}
#include "restart-terminal-iapp.c"
#include "restart-iapp-policy.h"
#undef WR_IOT_IAPP_POLICY_PREPARED
#define WR_IOT_IAPP_POLICY_PREPARED TEST_IAPP_GATE
#include "rc-cold-disabled-terminal.inc"
#include "rc-cold-disabled-completion.inc"
int main(int argc,char**argv){
 (void)check;assert(argc==4);led_failure=argv[3][0]-'0';disabled_plan=argv[2][0]-'0';assert(disabled_plan>=0&&disabled_plan<=2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_cold_owner owner={0};struct wr_iot_cold_disabled disabled={0};struct wr_iot_control_request input={0};
 down=1;partial=idle_fault=idle_reads=up_calls=generator_calls=attaches=0;membership=1;make_profile();
 guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
 bridge_fail=no_submit=service_fail=service_calls=mc_calls=mc_fail=0;up_result=WR_RESTART_UP_RETURNED;
 memset(input.id,'0',32);input.id[1]='1';input.created=7;
 assert(wr_iot_cold_owner_begin(&owner,&input,1));
 int ready=0;for(int i=0;i<40;i++)if(wr_iot_cold_owner_step(&owner)){ready=1;break;}
 assert(ready&&up_calls==1&&guest_ups==1&&generator_calls==1);
 assert(wr_iot_cold_disabled_begin(&disabled,&owner)&&!wr_iot_cold_disabled_begin(&disabled,&owner));
 assert(wr_iot_cold_disabled_current(&disabled));
 disabled.idle.idle.epoch--;assert(!wr_iot_cold_disabled_current(&disabled));disabled.idle.idle.epoch++;
 disabled.idle.idle.generation++;assert(!wr_iot_cold_disabled_current(&disabled));disabled.idle.idle.generation--;
 disabled.idle.created++;assert(!wr_iot_cold_disabled_current(&disabled));disabled.idle.created--;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_disabled_current(&disabled));wr_iot_rc_shutdown.pending=0;
 strcpy(saved_enabled,"1");assert(!wr_iot_cold_disabled_current(&disabled));strcpy(saved_enabled,"0");
 assert(wr_iot_cold_disabled_current(&disabled)&&owner.admission.profile.active&&depth==1);
 struct wr_iot_cold_disabled_release release={0};wan_policy=0;
 assert(wr_iot_cold_disabled_release_begin(&release,&disabled)&&release.owner==getpid());
 assert(!wr_iot_cold_disabled_release_current(&release)&&wan_captures==1);
 wan_policy=1;assert(wr_iot_cold_disabled_release_current(&release)&&wan_captures==1);
 release.created++;assert(!wr_iot_cold_disabled_release_current(&release));release.created--;
 release.identity.device_generation++;assert(!wr_iot_cold_disabled_release_current(&release));release.identity.device_generation--;
 auth=0;assert(!wr_iot_cold_disabled_release_current(&release));auth=1;
 aux=0;assert(!wr_iot_cold_disabled_release_current(&release));aux=1;
 assert(wr_iot_cold_disabled_release_current(&release)&&depth==1&&owner.admission.profile.active);
 assert(!wr_iot_wan_followup_step(&release.wan));

 struct wr_iot_cold_disabled_parent_release parent_release={0};
 backend.owner=getpid();backend.phase=WR_IOT_OWNER_ACTIVE;
 assert(!wr_iot_rc_cold_disabled_parent_release(&parent_release,&release)&&depth==1);
 memset(&backend,0,sizeof(backend));
 fail_disabled_unmask=1;
 assert(!wr_iot_rc_cold_disabled_parent_release(&parent_release,&release)&&!parent_release.released);
 assert(owner.admission.profile.active&&depth==1&&!backend.owner);
 fail_disabled_unmask=0;
 assert(wr_iot_rc_cold_disabled_parent_release(&parent_release,&release)&&parent_release.released);
 assert(!depth&&!owner.owner&&!owner.admission.profile.files.count&&!owner.admission.fence.owner);
 assert(!disabled.owner&&!release.parent&&!release.disabled);
 assert(backend.owner==getpid()&&backend.phase==WR_IOT_OWNER_INITIAL_OFF&&!backend.start.owner&&!backend.stop.owner);
 assert(!strcmp(backend.initial_off.id,release.id)&&backend.initial_off.created==release.created);
 assert(backend.initial_off.idle.epoch==release.identity.adapter_epoch&&backend.initial_off.idle.generation==release.identity.device_generation);
 assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned&&wr_iot_rc_shutdown.radio_on_owned);
 assert(!wr_iot_rc_cold_disabled_parent_release(&parent_release,&release));
 for(size_t j=0;j<sizeof(owner.generation);j++)assert(!((unsigned char*)&owner.generation)[j]);
 assert(wr_iot_cold_disabled_followup_current(&release)&&!depth);
 auth=0;assert(!wr_iot_cold_disabled_followup_wan(&release)&&!release.wan.attempted);auth=1;
 assert(wr_iot_cold_disabled_followup_wan(&release)==(disabled_plan==WR_WAN_NONE));
 assert(release.wan.attempted&&release.wan.returned&&wan_submits==(disabled_plan!=WR_WAN_NONE));
 if(disabled_plan!=WR_WAN_NONE)assert(!auth&&!wr_iot_cold_disabled_followup_wan(&release));
 auth=1;
 assert(wr_iot_cold_disabled_followup_wan(&release)&&wan_submits==(disabled_plan!=WR_WAN_NONE));
 release.created++;assert(!wr_iot_cold_disabled_followup_current(&release));release.created--;
 release.identity.device_generation++;assert(!wr_iot_cold_disabled_followup_current(&release));release.identity.device_generation--;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_disabled_followup_current(&release));wr_iot_rc_shutdown.pending=0;
 strcpy(saved_enabled,"1");assert(!wr_iot_cold_disabled_followup_current(&release));strcpy(saved_enabled,"0");
 assert(wr_iot_cold_disabled_followup_current(&release));
 guest_desired=0;assert(!wr_iot_cold_disabled_followup_current(&release));guest_desired=1;
 assert(wr_iot_cold_disabled_followup_current(&release)&&!depth&&!backend.start.owner);
 struct wr_iot_cold_disabled_terminal terminal_owner={0};
 led_calls=child_calls=0;child_outcome=disabled_plan==1?-1:disabled_plan==2?0:1;
 assert(wr_iot_rc_cold_disabled_terminal_begin(&terminal_owner,&parent_release));
 assert(!wr_iot_rc_cold_disabled_terminal_begin(&terminal_owner,&parent_release));
 auth=0;assert(!wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)&&!led_calls&&!child_calls);auth=1;
 assert(!wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)&&led_calls==1);
 if(led_failure){
  for(int retry=0;retry<4;retry++)assert(!wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)&&led_calls==1&&!child_calls);
  assert(terminal_owner.phase==WR_COLD_DISABLED_TERM_RETAINED&&!wr_iot_rc_cold_disabled_terminal_retire(&terminal_owner));
  wr_iot_rc_shutdown.radio_on_owned=0;assert(!unlink(profile_path));return 0;
 }
 if(!WR_IOT_IAPP_POLICY_PREPARED){
  for(int wait=0;wait<4;wait++)assert(!wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)&&!child_calls&&!wr_iot_rc_shutdown.active);
  assert(terminal_owner.phase==WR_COLD_DISABLED_TERM_IAPP_PENDING);
 }else{
  assert(!wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)&&wr_iot_rc_shutdown.active);
  assert(!wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)&&child_calls==1);
  if(disabled_plan==2){
   for(int wait=0;wait<3;wait++)assert(!wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)&&child_calls==1&&wr_iot_rc_shutdown.active);
   child_outcome=1;
  }
  assert(wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)==(disabled_plan!=1));
  assert(!depth&&!wr_iot_rc_shutdown.active&&led_calls==1&&child_calls==1);
  for(int repeat=0;repeat<3;repeat++)assert(wr_iot_rc_cold_disabled_terminal_step(&terminal_owner)==(disabled_plan!=1));
  if(disabled_plan!=1){
   auth=0;assert(!wr_iot_rc_cold_disabled_terminal_retire(&terminal_owner));auth=1;
   assert(wr_iot_rc_cold_disabled_terminal_retire(&terminal_owner)&&!terminal_owner.owner&&!release.owner&&!parent_release.release);
   assert(!wr_iot_rc_shutdown.radio_on_owned&&backend.phase==WR_IOT_OWNER_INITIAL_OFF&&!backend.start.owner);
  }else assert(!wr_iot_rc_cold_disabled_terminal_retire(&terminal_owner));
 }
 wr_iot_rc_shutdown.radio_on_owned=0;assert(!unlink(profile_path));

}

'''
body=body.replace('int wr_iot_bss_is_down(void){return down;}','int wr_iot_bss_is_down(void){return 1;}')
body=body.replace('#include "radio-stop-fence.c"',r'''static int fail_disabled_unmask;
static int disabled_mask(int how,const sigset_t *set,sigset_t *old){if(how==SIG_SETMASK&&fail_disabled_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask disabled_mask
#include "radio-stop-fence.c"
#undef sigprocmask
''')

with tempfile.TemporaryDirectory(prefix='wr-cold-owner-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 for gate in [0,1]:
  subprocess.run(['gcc','-DTEST_IAPP_GATE='+str(gate),'-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
  for plan in ['0','1','2']:
   for failed_led in ['0','1']:
    subprocess.run([str(b),d,plan,failed_led],check=True,timeout=20)
print('PASS disabled cold LED/IAPP/retirement: fresh new READY never-opened ra2, epoch/generation/envelope/pending/Guest/saved-policy drift refuse; active backend excluded, failed unmask retains, cleanup wipes profile/credentials/guard and publishes inert INITIAL_OFF; exact initial-OFF/profile/policy recheck, all WAN plans once despite post-call observation loss, no OPEN')
