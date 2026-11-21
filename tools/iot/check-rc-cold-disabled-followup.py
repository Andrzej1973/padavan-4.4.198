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
int main(int argc,char**argv){
 (void)check;assert(argc==3);disabled_plan=argv[2][0]-'0';assert(disabled_plan>=0&&disabled_plan<=2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
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
 assert(!wr_iot_cold_disabled_parent_release(&parent_release,&release)&&depth==1);
 memset(&backend,0,sizeof(backend));
 fail_disabled_unmask=1;
 assert(!wr_iot_cold_disabled_parent_release(&parent_release,&release)&&!parent_release.released);
 assert(owner.admission.profile.active&&depth==1&&!backend.owner);
 fail_disabled_unmask=0;
 assert(wr_iot_cold_disabled_parent_release(&parent_release,&release)&&parent_release.released);
 assert(!depth&&!owner.owner&&!owner.admission.profile.files.count&&!owner.admission.fence.owner);
 assert(!disabled.owner&&!release.parent&&!release.disabled);
 assert(backend.owner==getpid()&&backend.phase==WR_IOT_OWNER_INITIAL_OFF&&!backend.start.owner&&!backend.stop.owner);
 assert(!strcmp(backend.initial_off.id,release.id)&&backend.initial_off.created==release.created);
 assert(backend.initial_off.idle.epoch==release.identity.adapter_epoch&&backend.initial_off.idle.generation==release.identity.device_generation);
 assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned&&wr_iot_rc_shutdown.radio_on_owned);
 assert(!wr_iot_cold_disabled_parent_release(&parent_release,&release));
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

# Reuse the native snapshot provider from the existing desired-generation helper.
import ast
parsed=ast.parse((here/'check-cold-config-revision.py').read_text())
provider=next(ast.literal_eval(n.value) for n in parsed.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='provider' for t in n.targets))
prepared_body=body.replace('#include "check-generation-config-absent.h"',provider)
prepared_body=prepared_body.replace('#include "cold-on-generation.h"','#include "cold-on-generation.h"\n#include "generation-profile.h"',1)
anchor='make_profile();return 0;}\n#include "cold-on-admission.c"'
assert anchor in prepared_body
prepared_body=prepared_body.replace(anchor,r'''struct wr_iot_precreated_profile_request selected={0};
 assert(wr_iot_generation_profile_request(&selected)==1);
 FILE *in=tmpfile(),*out=fopen(profile_path,"w");assert(in&&out&&fputs(baseline,in)>=0);rewind(in);
 assert(wr_iot_precreated_profile(in,out,selected.ssid,selected.password,0));
 assert(!fclose(in)&&!fclose(out));return 0;}
#include "cold-on-admission.c"''')
anchor=' assert(wr_iot_cold_owner_begin(&owner,&input,1));'
assert anchor in prepared_body
prepared_body=prepared_body.replace(anchor,r'''
 struct wr_iot_saved_config config={.profile={.enabled=0,.ssid="IoT-B",.password="password-B",
  .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.10",.last="192.168.50.30"}};
 record_present=1;assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));
'''+anchor)
prepared_body=prepared_body.replace('strcpy(saved_enabled,"1");assert(!wr_iot_cold_disabled_current(&disabled));',
 'strcpy(saved_enabled,"1");assert(wr_iot_cold_disabled_current(&disabled));')
prepared_body=prepared_body.replace('strcpy(saved_enabled,"1");assert(!wr_iot_cold_disabled_followup_current(&release));',
 'strcpy(saved_enabled,"1");assert(wr_iot_cold_disabled_followup_current(&release));')
anchor=' assert(wr_iot_cold_disabled_followup_current(&release)&&!depth);'
assert anchor in prepared_body
prepared_body=prepared_body.replace(anchor,r'''
 strcpy(config.profile.ssid,"IoT-C");
 assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&config));
 assert(!wr_iot_restart_disabled_profile_current()); /* Legacy A is deliberately unchanged. */
'''+anchor)
final_source=(here/'rc-cold-final-shutdown.inc').read_text()
final_predicate=final_source[final_source.index('static int cold_final_initial_off('):final_source.index('static void cold_final_cleanup(')]
prepared_body=prepared_body.replace('int main(int argc,char**argv){',final_predicate+'\nint main(int argc,char**argv){')
anchor=' wr_iot_rc_shutdown.radio_on_owned=0;assert(!unlink(profile_path));'
assert anchor in prepared_body
prepared_body=prepared_body.replace(anchor,r'''
 assert(cold_final_initial_off(&release));
 release.identity.adapter_epoch++;assert(!cold_final_initial_off(&release));release.identity.adapter_epoch--;
 make_profile();assert(!wr_iot_cold_disabled_followup_current(&release)&&!cold_final_initial_off(&release));
'''+anchor)
# Extend this existing native B/A/C composition through actual terminal
# retirement and the shared backend-bound nonsecret profile history.
prepared_body=prepared_body.replace('static struct {pid_t owner;} rebind;',
 '#include "rebind-owner.h"\nstatic struct wr_iot_rebind_owner rebind;')
terminal=r'''
int wr_iot_activation_owner_observed(const struct wr_iot_activation_owner*s,const struct wr_iot_control_result*r){
 assert(s==&backend&&depth&&s->phase==WR_IOT_OWNER_INITIAL_OFF);
 return r->state==WR_IOT_RESULT_APPLIED&&r->created==s->initial_off.created&&
  !strcmp(r->id,s->initial_off.id)&&wr_iot_initial_off_observed(&s->initial_off);
}
int wr_iot_rebind_owner_observed(const struct wr_iot_rebind_owner*s,const struct wr_iot_control_result*r){(void)s;(void)r;assert(0);return 0;}
#include "rc-profile-history.inc"
static int history_leds,history_children;
int wr_iot_rc_restart_led_on(void){history_leds++;return 1;}
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*s){history_children++;s->owner=getpid();s->attempted=1;s->fd=9;return 1;}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){s->fd=-1;s->result=1;return 1;}
#include "restart-terminal-iapp.c"
#include "restart-iapp-policy.h"
#undef WR_IOT_IAPP_POLICY_PREPARED
#define WR_IOT_IAPP_POLICY_PREPARED 1
#include "rc-cold-disabled-terminal.inc"
'''
prepared_body=prepared_body.replace('int main(int argc,char**argv){',terminal+'\nint main(int argc,char**argv){')
anchor=' make_profile();assert(!wr_iot_cold_disabled_followup_current(&release)&&!cold_final_initial_off(&release));'
assert prepared_body.count(anchor)==1
prepared_body=prepared_body.replace(anchor,r'''
 struct wr_iot_cold_disabled_terminal terminal={0};
 struct wr_iot_profile_binding observed={0};struct wr_iot_restart_profile_receipt receipt={0};
 assert(wr_iot_cold_disabled_terminal_begin(&terminal,&parent_release));
 int finished=0;for(int i=0;i<12&&!finished;i++)finished=wr_iot_cold_disabled_terminal_step(&terminal);
 assert(finished&&history_leds==1&&history_children==1);
 {int g=wr_iot_service_guard_enter(1);assert(!wr_iot_rc_profile_history_read(&observed,&receipt));wr_iot_service_guard_leave(g);}
 release.identity.device_generation++;assert(!wr_iot_cold_disabled_terminal_retire(&terminal));release.identity.device_generation--;
 assert(wr_iot_cold_disabled_terminal_retire(&terminal)&&!release.owner&&!terminal.owner&&!parent_release.release);
 assert(!wr_iot_rc_shutdown.radio_on_owned);
 {int g=wr_iot_service_guard_enter(1);
  assert(wr_iot_rc_profile_history_read(&observed,&receipt)&&observed.kind==WR_PROFILE_BACKEND_INITIAL_OFF);
  assert(observed.created==backend.initial_off.created&&observed.identity.adapter_epoch==backend.initial_off.idle.epoch);
  backend.initial_off.created++;assert(!wr_iot_rc_profile_history_read(&observed,&receipt)&&!receipt.valid);backend.initial_off.created--;
  assert(wr_iot_rc_profile_history_read(&observed,&receipt));
  make_profile();assert(!wr_iot_rc_profile_history_read(&observed,&receipt));
  wr_iot_service_guard_leave(g);
 }
''')

with tempfile.TemporaryDirectory(prefix='wr-cold-owner-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\nint nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((here.parent/'band-steering/settings-snapshot.h').read_bytes())
 p=root/'check.c';b=root/'check'
 for prepared,unit in ((0,body),(1,prepared_body)):
  p.write_text(unit)
  extra=[str(here.parent/'band-steering/settings-snapshot.c')] if prepared else []
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED='+str(prepared),'-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20','-I'+d,'-I'+str(here),str(p),*extra,'-o',str(b)],check=True)
  for plan in ['0','1','2']:
   subprocess.run([str(b),d,plan],check=True,timeout=20)
print('PASS disabled cold native desired B -> generation/initial-OFF/cleanup/followup with legacy A and later C, three WAN plans; final shutdown predicate, epoch and foreign file refusal; default legacy regression; SDK/driver actors injected')
