"""Actual cold owner/parent/profile chain and handoff; initial runner and full ACTIVE transport injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-cold-on-owner.py').read_text()
ns={'__file__':str(here/'check-cold-on-owner.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
#include "rc-cold-start.h"
static int begins,continues,claim=1,active_proof,aux=1,auth=1;
int wr_iot_on_aux_down_current(void){return aux;}
int wr_iot_rc_restart_auth_process_current(const struct wr_iot_restart_service_policy*p){assert(p->enterprise==1);return auth;}
#include "activation-owner.h"
static struct wr_iot_activation_owner backend;
static struct {pid_t owner;} rebind;
int wr_iot_start_runner_begin(struct wr_iot_start_runner*p,const struct wr_iot_control_request*r,int a,int b,int c){
 assert(a==1&&b==1&&c==0&&r->created==7);begins++;if(!claim)return 0;
 p->owner=getpid();p->phase=WR_IOT_RUN_STAGE;p->input=*r;p->admission.admitted=1;
 p->admission.idle=(struct wr_iot_idle_result){5,2,9};return 1;
}
enum wr_iot_result_state wr_iot_activation_owner_continue(struct wr_iot_activation_owner*p,const char*id,unsigned long long created){
 assert(p==&backend&&!strcmp(id,p->start.input.id)&&created==7);continues++;
 p->phase=WR_IOT_OWNER_ACTIVE;p->start.phase=WR_IOT_RUN_ACTIVE;p->start.open.attempt.identity=(struct wr_iot_driver_identity){5,2};return WR_IOT_RESULT_APPLIED;
}
int wr_iot_activation_owner_observed(const struct wr_iot_activation_owner*p,const struct wr_iot_control_result*r){assert(p==&backend&&r->state==WR_IOT_RESULT_APPLIED);return active_proof;}
#include "rc-cold-start.inc"
#include "cold-on-handoff.c"
#include "restart-wan-followup.h"
static int wan_current=1,wan_capture_calls,wan_submits,wan_plan,lose_active_after_wan;
int wr_iot_rc_restart_wan_plan(int on,enum wr_iot_wan_followup*out){assert(on==1);wan_capture_calls++;*out=(enum wr_iot_wan_followup)wan_plan;return 1;}
int wr_iot_rc_restart_wan_current(int on,enum wr_iot_wan_followup plan){assert(on==1&&plan==(enum wr_iot_wan_followup)wan_plan);return wan_current;}
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup plan){assert(plan==(enum wr_iot_wan_followup)wan_plan);wan_submits++;if(lose_active_after_wan)active_proof=0;}
#include "restart-wan-followup.c"
#include "cold-on-policy.c"
#include "cold-on-release.c"
#include "rc-cold-detach.inc"
#include "rc-cold-release.inc"
#include "rc-cold-followup.inc"
#include "restart-terminal-iapp.h"
static int led_calls,child_calls,child_outcome;
int wr_iot_rc_restart_led_on(void){led_calls++;return 1;}
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*s){assert(!s->owner);child_calls++;s->owner=getpid();s->attempted=1;s->fd=9;return 1;}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){if(child_outcome==0)return -2;s->fd=-1;s->result=child_outcome;return child_outcome;}
#include "restart-terminal-iapp.c"
#include "restart-iapp-policy.h"
#undef WR_IOT_IAPP_POLICY_PREPARED
#define WR_IOT_IAPP_POLICY_PREPARED TEST_IAPP_GATE
#include "rc-cold-terminal.inc"
#include "rc-cold-completion.inc"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.30.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.30.10");strcpy(desired.last,"192.168.30.40");
 for(wan_plan=0;wan_plan<=2;wan_plan++)for(int fault=0;fault<3;fault++){
  struct wr_iot_cold_owner owner={0};struct wr_iot_cold_handoff handoff={0};struct wr_iot_control_request input={0};
  down=1;partial=idle_fault=idle_reads=up_calls=generator_calls=attaches=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
  bridge_fail=no_submit=service_fail=service_calls=mc_calls=mc_fail=0;up_result=WR_RESTART_UP_RETURNED;
  memset(&backend,0,sizeof(backend));wr_iot_cold_backend_parent=NULL;memset(&wr_iot_cold_backend_identity,0,sizeof(wr_iot_cold_backend_identity));
  begins=continues=active_proof=0;claim=fault!=1;aux=auth=1;
  memset(input.id,'0',32);input.id[1]='1';input.created=7;input.request=desired;
  assert(wr_iot_cold_owner_begin(&owner,&input,1));
  int ready=0;for(int i=0;i<40;i++)if(wr_iot_cold_owner_step(&owner)){ready=1;break;}
  assert(ready&&up_calls==1&&guest_ups==1);
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_handoff_begin(&handoff,&owner)&&!begins&&!handoff.owner);wr_iot_rc_shutdown.pending=0;
  aux=0;assert(!wr_iot_cold_handoff_begin(&handoff,&owner)&&!begins);aux=1;
  assert(wr_iot_cold_handoff_begin(&handoff,&owner)&&begins==1);
  assert(!wr_iot_cold_handoff_begin(&handoff,&owner)&&begins==1);
  assert(!wr_iot_cold_handoff_current(&handoff)&&!continues);
  assert(!wr_iot_cold_handoff_step(&handoff)&&continues==(claim?1:0));
  if(claim){
   active_proof=fault!=2;
   if(active_proof){
    struct wr_iot_cold_release release={0};wan_capture_calls=wan_submits=lose_active_after_wan=0;wan_current=0;
    assert(wr_iot_cold_release_begin(&release,&handoff)&&release.owner==getpid());
    assert(!wr_iot_cold_release_begin(&release,&handoff)&&!wr_iot_cold_release_current(&release));
    assert(wan_capture_calls==1&&!wan_submits&&owner.admission.profile.active&&depth==1);
    wan_current=1;assert(wr_iot_cold_release_current(&release)&&wan_capture_calls==1);
    release.created++;assert(!wr_iot_cold_release_current(&release));release.created--;
    release.identity.adapter_epoch++;assert(!wr_iot_cold_release_current(&release));release.identity.adapter_epoch--;
    release.parent=NULL;assert(!wr_iot_cold_release_current(&release));release.parent=&owner;
    assert(wr_iot_cold_release_current(&release)&&wan_capture_calls==1);
    assert(!wr_iot_wan_followup_step(&release.wan)&&!wan_submits);
    wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_release_current(&release));wr_iot_rc_shutdown.pending=0;
    release.wan.attempted=1;assert(!wr_iot_cold_release_current(&release));release.wan.attempted=0;
    assert(wr_iot_cold_release_current(&release));
    struct wr_iot_cold_parent_release parent_release={0};
    struct wr_iot_activation_owner backend_before=backend;
    fail_release_unmask=1;
    assert(!wr_iot_rc_cold_parent_release(&parent_release,&release)&&!parent_release.released);
    assert(wr_iot_cold_backend_parent==&owner&&owner.admission.profile.active&&depth==1);
    assert(!memcmp(&backend,&backend_before,sizeof(backend))&&wr_iot_rc_shutdown.active);
    fail_release_unmask=0;
    assert(wr_iot_rc_cold_parent_release(&parent_release,&release)&&parent_release.released);
    assert(!memcmp(&backend,&backend_before,sizeof(backend))&&!wr_iot_cold_backend_parent);
    assert(!owner.owner&&!owner.admission.profile.active&&!owner.admission.profile.files.count&&!depth);
    assert(!owner.admission.fence.owner&&!handoff.owner&&!release.parent&&!release.handoff);
    for(size_t j=0;j<sizeof(owner.generation);j++)assert(!((unsigned char*)&owner.generation)[j]);
    assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned&&wr_iot_rc_shutdown.radio_on_owned);
    assert(!wr_iot_rc_cold_parent_release(&parent_release,&release)&&!wan_submits);
    assert(wr_iot_cold_followup_active(&release)&&!depth);
    guest_desired=0;assert(!wr_iot_cold_followup_active(&release));guest_desired=1;
    auth=0;assert(!wr_iot_cold_followup_active(&release));auth=1;
    mc_fail=1;assert(!wr_iot_cold_followup_active(&release));mc_fail=0;
    release.policy.services.kick_rssi++;assert(!wr_iot_cold_followup_active(&release));release.policy.services.kick_rssi--;
    assert(wr_iot_cold_followup_active(&release));
    wan_current=0;assert(!wr_iot_cold_followup_wan(&release)&&!release.wan.attempted);wan_current=1;
    lose_active_after_wan=1;
    assert(wr_iot_cold_followup_wan(&release)==(wan_plan==WR_WAN_NONE));
    assert(release.wan.attempted&&release.wan.returned&&wan_submits==(wan_plan!=WR_WAN_NONE));
    if(wan_plan!=WR_WAN_NONE)assert(!active_proof&&!wr_iot_cold_followup_wan(&release));
    active_proof=1;lose_active_after_wan=0;
    assert(wr_iot_cold_followup_wan(&release)&&wan_submits==(wan_plan!=WR_WAN_NONE));
    active_proof=0;assert(!wr_iot_cold_followup_active(&release));active_proof=1;
    release.identity.adapter_epoch++;assert(!wr_iot_cold_followup_active(&release));release.identity.adapter_epoch--;
    release.created++;assert(!wr_iot_cold_followup_active(&release));release.created--;
    wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_cold_followup_active(&release));wr_iot_rc_shutdown.pending=0;
    assert(wr_iot_cold_followup_active(&release));
    struct wr_iot_cold_terminal terminal_owner={0};led_calls=child_calls=0;child_outcome=wan_plan==1?-1:wan_plan==2?0:1;
    assert(wr_iot_rc_cold_terminal_begin(&terminal_owner,&parent_release));
    assert(!wr_iot_rc_cold_terminal_begin(&terminal_owner,&parent_release));
    active_proof=0;assert(!wr_iot_rc_cold_terminal_step(&terminal_owner)&&!led_calls&&!child_calls);active_proof=1;
    assert(!wr_iot_rc_cold_terminal_step(&terminal_owner)&&led_calls==1);
    if(!WR_IOT_IAPP_POLICY_PREPARED){
     for(int wait=0;wait<4;wait++)assert(!wr_iot_rc_cold_terminal_step(&terminal_owner)&&!child_calls&&!wr_iot_rc_shutdown.active);
     assert(terminal_owner.phase==WR_COLD_TERM_IAPP_PENDING&&led_calls==1);
     wr_iot_rc_shutdown.radio_on_owned=0;assert(!unlink(profile_path));continue;
    }
    assert(!wr_iot_rc_cold_terminal_step(&terminal_owner)&&wr_iot_rc_shutdown.active);
    assert(!wr_iot_rc_cold_terminal_step(&terminal_owner)&&child_calls==1);
    if(wan_plan==2){
     for(int wait=0;wait<3;wait++)assert(!wr_iot_rc_cold_terminal_step(&terminal_owner)&&child_calls==1&&wr_iot_rc_shutdown.active);
     child_outcome=1;
    }
    assert(wr_iot_rc_cold_terminal_step(&terminal_owner)==(wan_plan!=1));
    assert(!wr_iot_rc_shutdown.active&&!depth&&led_calls==1&&child_calls==1);
    for(int repeat=0;repeat<3;repeat++)assert(wr_iot_rc_cold_terminal_step(&terminal_owner)==(wan_plan!=1));
    assert(led_calls==1&&child_calls==1&&wan_submits==(wan_plan!=WR_WAN_NONE));
    if(wan_plan!=1){
     active_proof=0;assert(!wr_iot_rc_cold_terminal_retire(&terminal_owner)&&wr_iot_rc_shutdown.radio_on_owned);active_proof=1;
     assert(wr_iot_rc_cold_terminal_retire(&terminal_owner)&&!terminal_owner.owner&&!parent_release.release&&!release.owner);
     assert(!wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_cold_terminal_retire(&terminal_owner));
     assert(!memcmp(&backend,&backend_before,sizeof(backend)));
     assert(!unlink(profile_path));continue;
    }
    assert(!wr_iot_rc_cold_terminal_retire(&terminal_owner));
    FILE*changed=fopen(profile_path,"a");assert(changed&&fputs("# foreign change\n",changed)>=0&&!fclose(changed));
    assert(!wr_iot_cold_followup_active(&release)&&!depth&&wan_submits==(wan_plan!=WR_WAN_NONE));
    assert(!memcmp(&backend,&backend_before,sizeof(backend)));
    wr_iot_rc_shutdown.radio_on_owned=0;assert(!unlink(profile_path));continue;
   }
   assert(wr_iot_cold_handoff_current(&handoff)==active_proof&&continues==1);
   guest_desired=0;assert(!wr_iot_cold_handoff_step(&handoff)&&continues==1);guest_desired=1;
   owner.main.identity.adapter_epoch++;assert(!wr_iot_cold_handoff_step(&handoff)&&continues==1);owner.main.identity.adapter_epoch--;
   auth=0;assert(!wr_iot_cold_handoff_step(&handoff)&&continues==1);auth=1;
   assert(wr_iot_cold_handoff_step(&handoff)==active_proof&&continues==1);
  }else assert(handoff.phase==WR_COLD_HANDOFF_RETAINED);
  assert(owner.admission.profile.active&&owner.admission.busy&&depth==1&&!wr_iot_cold_owner_recover(&owner));
  /* Fixture cleanup only: post-UP shutdown/retirement remains unbound. */
  wr_iot_bundle_release(&owner.admission.profile.files);memset(&owner.admission.profile,0,sizeof(owner.admission.profile));owner.admission.busy=0;
  assert(wr_iot_cold_admission_cancel(&owner.admission)&&!depth);assert(!unlink(profile_path));
 }
}
'''
body=body.replace('#include "radio-stop-fence.c"',r'''static int fail_release_unmask;
static int release_mask(int how,const sigset_t *set,sigset_t *old){if(how==SIG_SETMASK&&fail_release_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask release_mask
#include "radio-stop-fence.c"
#undef sigprocmask
''')

with tempfile.TemporaryDirectory(prefix='wr-cold-handoff-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 for gate in [0,1]:
  subprocess.run(['gcc','-DTEST_IAPP_GATE='+str(gate),'-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
  subprocess.run([str(b),d],check=True,timeout=20)
print('PASS cold terminal owner actual parent cleanup/WAN/fence/IAPP terminal: one begin even on refusal, exact identity/envelope, retained profile/guard, no ACTIVE shortcut, pending/Guest/auth/aux drift gates; backend preserved; binding/credentials/profile/guard cleared inside real fence; NONE no submit; restart/reconnect once despite post-call ACTIVE loss; no parent/credentials, exact envelope/driver/profile, false APPLIED/drift refusal; child pipe and SDK actors; uncomposed')
