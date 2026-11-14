"""Exact SDK radio/reload state adapter, fixed keys and readback; no RF claim."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "restart-radio-state.h"
static int guard=1,ap,mode,radio=1,down=1,reload_value=7,mlme_value,writes,fail_reload,fail_mlme;
static int wr_iot_service_guard_dup(void){return guard?9:-1;}
static int close(int fd){assert(fd==9);return 0;}
static int get_ap_mode(void){return ap;}
static int get_mode_radio_rt(void){return mode;}
static int get_enabled_radio_rt(void){return radio;}
static int wr_iot_restart_main_down(void){return down;}
static void nvram_set_int_temp(const char*k,int v){assert(!strcmp(k,"reload_svc_rt")&&v==1);writes++;if(!fail_reload)reload_value=v;}
static int nvram_get_int(const char*k){if(!strcmp(k,"reload_svc_rt"))return reload_value;assert(!strcmp(k,"mlme_radio_rt"));return mlme_value;}
static void mlme_state_rt(int v){assert(v==1);writes++;if(!fail_mlme)mlme_value=v;}
#include "restart-radio-state-sdk.inc"
int main(void){
 assert(!wr_iot_rc_restart_radio_state(2)&&!writes);
 guard=0;assert(!wr_iot_rc_restart_radio_state(1)&&!writes);guard=1;
 ap=1;assert(!wr_iot_rc_restart_radio_state(1)&&!writes);ap=0;
 mode=2;assert(!wr_iot_rc_restart_radio_state(1)&&!writes);mode=0;
 radio=0;assert(!wr_iot_rc_restart_radio_state(1)&&!writes);radio=1;
 down=0;assert(!wr_iot_rc_restart_radio_state(1)&&!writes);down=1;
 assert(wr_iot_rc_restart_radio_state(0)&&writes==1&&reload_value==7&&mlme_value==1);
 writes=0;mlme_value=0;fail_reload=1;
 assert(!wr_iot_rc_restart_radio_state(1)&&writes==1&&reload_value==7&&!mlme_value);
 writes=0;fail_reload=0;fail_mlme=1;
 assert(!wr_iot_rc_restart_radio_state(1)&&writes==2&&reload_value==1&&!mlme_value);
 writes=0;fail_mlme=0;assert(wr_iot_rc_restart_radio_state(1)&&writes==2);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-radio-state-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS SDK radio/reload state adapter: guard/mode/radio/Main-DOWN gates, fixed keys, reload0 preserves flag, reload/MLME readback failures refuse, no commit or RF operation; SDK actors injected')
