from pathlib import Path
import tempfile,subprocess
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "radio-off-policy.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int guard=1,ap,mode,radio=1,auth=1,drift,reads,plans;
static enum wr_iot_wan_followup wan=WR_WAN_NONE;
int wr_iot_service_guard_dup(void){return guard?dup(1):-1;}
int get_ap_mode(void){return ap;}
int get_mode_radio_rt(void){return mode;}
int get_enabled_radio_rt(void){reads++;return drift&&reads==2?!radio:radio;}
const char *nvram_wlan_get(int band,const char*key){assert(!band&&!strcmp(key,"auth_mode"));return "fixture";}
int is_need_8021x(const char*s){assert(!strcmp(s,"fixture"));return auth;}
int wr_iot_rc_restart_wan_plan(int on,enum wr_iot_wan_followup*out){assert(!on);plans++;*out=wan;return 1;}
#include "radio-off-policy-sdk.inc"
int main(void){
 struct wr_iot_radio_off_policy p={0},sentinel;
 memset(&sentinel,0x5a,sizeof(sentinel));p=sentinel;
 assert(!wr_iot_rc_radio_off_policy(0,&p)&&!memcmp(&p,&sentinel,sizeof(p)));
 wr_iot_rc_shutdown.active=1;
 for(int r=0;r<=1;r++)for(int a=0;a<=1;a++)for(int reload=0;reload<=1;reload++){
  radio=r;auth=a;reads=0;assert(wr_iot_rc_radio_off_policy(reload,&p));
  assert(p.reload==reload&&p.stored_radio==r&&p.auth_required==(r&&a)&&p.wan==WR_WAN_NONE);
 }
 p=sentinel;radio=1;reads=0;drift=1;assert(!wr_iot_rc_radio_off_policy(0,&p)&&!memcmp(&p,&sentinel,sizeof(p)));drift=0;
 wan=WR_WAN_RECONNECT;assert(!wr_iot_rc_radio_off_policy(0,&p));wan=WR_WAN_FULL_RESTART;
 assert(wr_iot_rc_radio_off_policy(1,&p)&&p.wan==WR_WAN_FULL_RESTART);
 guard=0;assert(!wr_iot_rc_radio_off_policy(0,&p));guard=1;
 ap=1;assert(!wr_iot_rc_radio_off_policy(0,&p));ap=0;
 mode=1;assert(!wr_iot_rc_radio_off_policy(0,&p));mode=0;
 radio=2;assert(!wr_iot_rc_radio_off_policy(0,&p));radio=1;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_rc_radio_off_policy(0,&p));
 assert(!wr_iot_rc_radio_off_policy(2,&p)&&!wr_iot_rc_radio_off_policy(0,0));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-policy-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS read-only OFF SDK policy: admission/guard/router/mode, stored-radio/auth/reload combinations, drift/output-preserving refusal, OFF WAN no reconnect; SDK actors injected, unbound')
