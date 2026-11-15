from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "radio-off-state.h"
static int guard=1,ap,mode,radio=1,value=1,reload_value=7,writes,observe=1,reads,fail_mlme,post_fail;
static int wr_iot_service_guard_dup(void){return guard?9:-1;}
static int close(int fd){assert(fd==9);return 0;}
static int get_ap_mode(void){return ap;}
static int get_mode_radio_rt(void){return mode;}
static int get_enabled_radio_rt(void){return radio;}
static int wr_iot_radio_off_observed(const struct wr_iot_physical_stop_request*r){assert(r->action==WR_STOP_RELEASE);reads++;return observe&&!(post_fail&&reads==2);}
static void nvram_set_int_temp(const char*k,int v){assert(!strcmp(k,"reload_svc_rt")&&v==1);writes++;reload_value=v;}
static void mlme_state_rt(int v){assert(!v);writes++;if(!fail_mlme)value=v;}
static int nvram_get_int(const char*k){assert(!strcmp(k,"mlme_radio_rt"));return value;}
#define nvram_commit forbidden_commit
#include "radio-off-state-sdk.inc"
int main(void){
 struct wr_iot_radio_off_policy p={0,1,0,WR_WAN_NONE};
 struct wr_iot_physical_stop_request r={WR_STOP_RELEASE,1,2,3,4,5,{1}};
 guard=0;assert(!wr_iot_rc_radio_off_state(&p,&r)&&!writes);guard=1;
 ap=1;assert(!wr_iot_rc_radio_off_state(&p,&r)&&!writes);ap=0;
 mode=1;assert(!wr_iot_rc_radio_off_state(&p,&r)&&!writes);mode=0;
 radio=0;assert(!wr_iot_rc_radio_off_state(&p,&r)&&!writes);radio=1;
 observe=0;assert(!wr_iot_rc_radio_off_state(&p,&r)&&!writes);observe=1;
 reads=0;assert(wr_iot_rc_radio_off_state(&p,&r)&&writes==1&&reload_value==7&&!value);
 p.reload=1;reads=writes=0;value=1;fail_mlme=1;
 assert(!wr_iot_rc_radio_off_state(&p,&r)&&writes==2&&reload_value==1&&value==1);fail_mlme=0;
 reads=writes=0;value=1;post_fail=1;assert(!wr_iot_rc_radio_off_state(&p,&r)&&writes==2&&!value);post_fail=0;
 radio=p.stored_radio=0;reads=writes=0;assert(wr_iot_rc_radio_off_state(&p,&r)&&writes==2);
 p.reload=2;assert(!wr_iot_rc_radio_off_state(&p,&r));assert(!wr_iot_rc_radio_off_state(0,&r));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-state-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS OFF SDK RAM state: guard/mode/stored-radio/fresh-DOWN gates, reload0 preserves event, mlme0 readback, partial/post-observation refusal, no commit/RF operation; SDK actors injected, unbound')
