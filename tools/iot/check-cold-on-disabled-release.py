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
static int auth=1,aux=1,wan_policy=1,wan_captures;
int wr_iot_on_aux_down_current(void){return aux;}
int wr_iot_rc_restart_auth_process_current(const struct wr_iot_restart_service_policy*p){assert(p->enterprise==1);return auth;}
#include "cold-on-policy.c"
#include "restart-wan-followup.h"
int wr_iot_rc_restart_wan_plan(int radio,enum wr_iot_wan_followup*out){assert(radio==1);wan_captures++;*out=WR_WAN_NONE;return 1;}
int wr_iot_rc_restart_wan_current(int radio,enum wr_iot_wan_followup plan){assert(radio==1&&plan==WR_WAN_NONE);return wan_policy;}
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup plan){(void)plan;assert(0);}
#include "restart-wan-followup.c"
#include "cold-on-disabled-release.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
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
 guest_desired=0;assert(!wr_iot_cold_disabled_release_current(&release));assert(!wr_iot_cold_disabled_current(&disabled));guest_desired=1;
 assert(!wr_iot_cold_disabled_current(&disabled)); /* Guest DOWN recovery is not undone. */
 assert(!wr_iot_cold_owner_recover(&owner));
 /* Fixture teardown only: disabled release not implemented yet. */
 wr_iot_bundle_release(&owner.admission.profile.files);memset(&owner.admission.profile,0,sizeof(owner.admission.profile));owner.admission.busy=0;
 assert(wr_iot_cold_admission_cancel(&owner.admission)&&!depth);assert(!unlink(profile_path));
}

'''
body=body.replace('int wr_iot_bss_is_down(void){return down;}','int wr_iot_bss_is_down(void){return 1;}')
with tempfile.TemporaryDirectory(prefix='wr-cold-owner-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=20)
print('PASS cold disabled release preparation: fresh new READY never-opened ra2, epoch/generation/envelope/pending/Guest/saved-policy drift refuse; policy/profile/WAN captured once, refusal retains parent/guard; no OPEN/fabricated RELEASE or WAN submit')
