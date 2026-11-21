from pathlib import Path
import tempfile,subprocess
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "radio-off-auth.h"
#define IFNAME_2G_MAIN "ra0"
static int guard=1,radio,enterprise,up,observed=1,launches,failed,reads,drift;
int wr_iot_service_guard_dup(void){return guard?9:-1;}
int close(int fd){assert(fd==9);return 0;}
int get_enabled_radio_rt(void){return radio;}
int get_ap_mode(void){return 0;}
int get_mode_radio_rt(void){return 0;}
char *nvram_wlan_get(int b,const char*k){assert(!b&&!strcmp(k,"auth_mode"));return enterprise?"wpa2":"psk";}
int is_need_8021x(char*s){return !strcmp(s,"wpa2");}
const char *find_wlan_if_up(int b){assert(!b);return up?"ra1":0;}
int wr_iot_radio_off_observed(const struct wr_iot_physical_stop_request*r){assert(r->action==WR_STOP_RELEASE);reads++;return observed&&!(drift&&reads==3);}
int eval(const char*a,const char*b,const char*c){assert(!strcmp(a,"rtinicapd")&&!strcmp(b,"-i")&&!strcmp(c,"ra0"));launches++;return failed;}
#define doSystem forbidden_RSSI_write
#include "radio-off-auth-sdk.inc"
int main(void){
 struct wr_iot_physical_stop_request r={.action=WR_STOP_RELEASE};
 for(radio=0;radio<2;radio++)for(enterprise=0;enterprise<2;enterprise++){
  struct wr_iot_radio_off_policy p={.stored_radio=radio,.auth_required=radio&&enterprise};launches=reads=0;
  assert(wr_iot_rc_radio_off_auth(&p,&r)==WR_OFF_AUTH_RETURNED&&launches==p.auth_required);
 }
 radio=enterprise=1;struct wr_iot_radio_off_policy p={.stored_radio=1,.auth_required=1};launches=0;
 up=1;assert(wr_iot_rc_radio_off_auth(&p,&r)==WR_OFF_AUTH_REFUSED&&!launches);up=0;
 guard=0;assert(wr_iot_rc_radio_off_auth(&p,&r)==WR_OFF_AUTH_REFUSED);guard=1;
 observed=0;assert(wr_iot_rc_radio_off_auth(&p,&r)==WR_OFF_AUTH_REFUSED);observed=1;
 failed=1;assert(wr_iot_rc_radio_off_auth(&p,&r)==WR_OFF_AUTH_UNCERTAIN&&launches==1);failed=0;
 reads=0;drift=1;assert(wr_iot_rc_radio_off_auth(&p,&r)==WR_OFF_AUTH_UNCERTAIN&&launches==2);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-auth-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS OFF SDK auth: stored-radio/auth combinations, exact enterprise launch, no RSSI commands, UP/guard/DOWN refusal and post-submit uncertainty; SDK actors injected, unbound')
