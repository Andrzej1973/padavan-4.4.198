from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'prepare-rc.py').read_text())
helper=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets))
a=helper.index('int wr_iot_rc_restart_service_policy(');b=helper.index('/* Profile generation only;',a)
code=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "restart-service-policy.h"
#define IFNAME_2G_MAIN "ra0"
static int guard=1,ap,mode,radio=1,up=1,enterprise,kick=-75,assoc=-80,calls,fail,drift,reads,running;
static int wr_iot_service_guard_dup(void){return guard?9:-1;}
static int close(int fd){assert(fd==9);return 0;}
static int get_ap_mode(void){return ap;}
static int get_mode_radio_rt(void){return mode;}
static int get_enabled_radio_rt(void){return radio;}
static int is_interface_up(const char*n){assert(!strcmp(n,"ra0"));return up;}
static const char *nvram_wlan_get(int band,const char*k){assert(!band&&!strcmp(k,"auth_mode"));return enterprise?"wpa2":"psk";}
static int is_need_8021x(const char*s){return !strcmp(s,"wpa2");}
static int nvram_get_int(const char*k){if(!strcmp(k,"rt_KickStaRssiLow")){reads++;return kick+(drift&&reads==2);}assert(!strcmp(k,"rt_AssocReqRssiThres"));return assoc;}
static int pids(const char*n){assert(!strcmp(n,"rtinicapd"));return running;}
static int eval(const char*a,const char*b,const char*c){assert(!strcmp(a,"rtinicapd")&&!strcmp(b,"-i")&&!strcmp(c,"ra0"));calls++;return fail;}
static int doSystem(const char*f,const char*n,const char*k,int v){assert(!strcmp(f,"iwpriv %s set %s=%d")&&!strcmp(n,"ra0"));assert((!strcmp(k,"KickStaRssiLow")&&v==kick)||(!strcmp(k,"AssocReqRssiThres")&&v==assoc));calls++;return fail;}
'''+helper[a:b]+r'''
int main(void){
 struct wr_iot_restart_service_policy p={77,77,77};
 for(int fault=0;fault<7;fault++){
  guard=fault!=0;ap=fault==1;mode=fault==2?2:0;radio=fault==3?0:1;up=fault!=4;drift=fault==5;reads=0;
  int ok=wr_iot_rc_restart_service_policy(&p);
  assert(ok==(fault==6));if(!ok)assert(p.enterprise==77&&p.kick_rssi==77&&p.assoc_rssi==77);
 }
 drift=0;
 int limits[]={-101,1,256,-300};
 for(unsigned i=0;i<sizeof(limits)/sizeof(limits[0]);i++){
  kick=limits[i];assoc=-80;reads=0;p.enterprise=77;
  assert(!wr_iot_rc_restart_service_policy(&p)&&p.enterprise==77);
  kick=-75;assoc=limits[i];reads=0;assert(!wr_iot_rc_restart_service_policy(&p)&&p.enterprise==77);
 }
 kick=-100;assoc=0;reads=0;assert(wr_iot_rc_restart_service_policy(&p));
 kick=-75;assoc=-80;reads=0;assert(wr_iot_rc_restart_service_policy(&p));
 running=0;assert(wr_iot_rc_restart_auth_process_current(&p));running=1;assert(!wr_iot_rc_restart_auth_process_current(&p));
 calls=0;assert(wr_iot_rc_restart_service_submit(&p,0)==WR_SERVICE_RETURNED&&!calls);
 for(int slot=1;slot<3;slot++){assert(wr_iot_rc_restart_service_submit(&p,slot)==WR_SERVICE_RETURNED);}
 assert(calls==2);enterprise=1;assert(wr_iot_rc_restart_service_submit(&p,0)==WR_SERVICE_NOT_SUBMITTED&&calls==2);
 assert(wr_iot_rc_restart_service_policy(&p));
 running=0;assert(!wr_iot_rc_restart_auth_process_current(&p));running=1;assert(wr_iot_rc_restart_auth_process_current(&p));running=-1;assert(!wr_iot_rc_restart_auth_process_current(&p));
 for(unsigned slot=0;slot<3;slot++){
  int before=calls;fail=1;assert(wr_iot_rc_restart_service_submit(&p,slot)==WR_SERVICE_UNCERTAIN&&calls==before+1);
 }
 assert(wr_iot_rc_restart_service_submit(&p,3)==WR_SERVICE_NOT_SUBMITTED);
 guard=0;int before=calls;assert(wr_iot_rc_restart_service_submit(&p,0)==WR_SERVICE_NOT_SUBMITTED&&calls==before);
 puts("PASS extracted mode0 service policy/submission: guard/mode/radio/Main/drift refusal, exact daemon/RSSI operations, nonenterprise no daemon, one operation per call, failure uncertain; SDK actors injected, not process/driver acceptance");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-service-policy-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
