from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-off-profile.py').read_text()
ns={'__file__':str(here/'check-radio-off-profile.py')}
exec(compile(source[:source.index('with tempfile.TemporaryDirectory(')],'<OFF profile fixture>','exec'),ns)
body=ns['body'].split('int main(int argc',1)[0]
body+=r'''
#include "radio-off-followup.h"
#include "radio-off-bridge.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int state_calls,state_fail;
static int mlme_value;
static int get_ap_mode(void){return 0;}
static int get_mode_radio_rt(void){return 0;}
static int get_enabled_radio_rt(void){return 0;}
static void nvram_set_int_temp(const char*k,int v){assert(depth&&!strcmp(k,"reload_svc_rt")&&v==1);}
static void mlme_state_rt(int on){assert(depth&&!on);state_calls++;if(!state_fail)mlme_value=on;}
static int nvram_get_int(const char*k){assert(!strcmp(k,"mlme_radio_rt"));return mlme_value;}
#include "radio-off-state-sdk.inc"
static unsigned bridge_calls;static int bridge_uncertain,bridge_refuse;
enum wr_iot_off_bridge_result wr_iot_radio_off_bridge_detach(const struct wr_iot_physical_stop_request*r,unsigned slot){
 assert(!depth&&state_calls==1&&r->action==WR_STOP_RELEASE&&slot==bridge_calls);
 if(bridge_refuse)return WR_OFF_BRIDGE_REFUSED;
 bridge_calls++;return bridge_uncertain?WR_OFF_BRIDGE_UNCERTAIN:WR_OFF_BRIDGE_DETACHED;
}
#include "radio-off-followup.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_radio_off_owner off={.owner=getpid(),.result=1,.policy_ready=1,.policy={.reload=1},.released={WR_STOP_RELEASE,1,2,3,4,5,{1}}};
 wr_iot_rc_shutdown.radio_off_owned=1;
 for(int fault=0;fault<4;fault++){
  struct wr_iot_off_followup s={0};make_profile();generator_calls=state_calls=0;partial=fault==1;state_fail=fault==2;mlme_value=1;bridge_calls=0;bridge_uncertain=fault==3;
  assert(wr_iot_off_followup_begin(&s,&off));assert(!wr_iot_off_followup_begin(&s,&off));
  off.policy.reload=0;assert(wr_iot_off_followup_step(&s)==WR_OFF_FOLLOWUP_PROFILE_BEGIN&&!generator_calls);off.policy.reload=1;
  off.released.attempt++;assert(wr_iot_off_followup_step(&s)==WR_OFF_FOLLOWUP_PROFILE_BEGIN&&!generator_calls);off.released.attempt--;
  wr_iot_rc_shutdown.pending=SIGTERM;assert(wr_iot_off_followup_step(&s)==WR_OFF_FOLLOWUP_PROFILE_BEGIN&&!generator_calls&&!state_calls);wr_iot_rc_shutdown.pending=0;
  for(int i=0;i<20&&s.phase!=WR_OFF_FOLLOWUP_NETWORK_PENDING&&s.phase!=WR_OFF_FOLLOWUP_RETAINED;i++)(void)wr_iot_off_followup_step(&s);
  assert(generator_calls==1&&s.profile.baseline.active&&!depth);
  assert(s.phase==(fault?WR_OFF_FOLLOWUP_RETAINED:WR_OFF_FOLLOWUP_NETWORK_PENDING));
  assert(state_calls==(fault!=1));assert(bridge_calls==(fault==0?7:fault==3?1:0));int before=state_calls;
  for(int i=0;i<3;i++)(void)wr_iot_off_followup_step(&s);
  assert(state_calls==before&&generator_calls==1&&wr_iot_rc_shutdown.radio_off_owned);
  /* Fixture-only free after proving ownership/baseline retained. */
  wr_iot_bundle_release(&s.profile.baseline.files);assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-followup-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS OFF profile-to-RAM followup: actual journal/scanner, generator once before state once, pending hold, restored/partial state retained, NETWORK_PENDING unfinished; actual SDK RAM adapter; SDK writes/DOWN injected, RC binding pending')
