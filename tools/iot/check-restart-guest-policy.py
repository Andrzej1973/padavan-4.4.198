from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
module=ast.parse((here/'prepare-rc.py').read_text())
helper=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets))
a=helper.index('int wr_iot_rc_restart_guest_policy(');b=helper.index('\n}',a)+2
a2=helper.index('int wr_iot_rc_restart_guest_isolation_policy(');b2=helper.index('\n}',a2)+2
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int ap,mode,radio=1,enabled,allowed,reads,drift,guard=1,closed,isolate_reads,mode_drift;
static int wr_iot_service_guard_dup(void){return guard?9:-1;}
static int close(int fd){assert(fd==9);closed++;return 0;}
static int get_ap_mode(void){return ap;}
static int get_mode_radio_rt(void){return mode;}
static int get_enabled_radio_rt(void){return radio;}
static int get_enabled_guest_rt(void){return enabled;}
static int nvram_wlan_get_int(int band,const char*key){assert(!band&&!strcmp(key,"guest_lan_isolate"));isolate_reads++;if(isolate_reads==2&&mode_drift){if(mode_drift==1)ap=1;if(mode_drift==2)mode=3;if(mode_drift==3)radio=0;}return enabled;}
static int is_guest_allowed_rt(void){reads++;return drift&&reads==2?!allowed:allowed;}
'''+helper[a:b]+helper[a2:b2]+r'''
int main(void){
 int out=77;
 assert(wr_iot_rc_restart_guest_policy(&out)&&!out);
 enabled=allowed=1;reads=0;assert(wr_iot_rc_restart_guest_policy(&out)&&out==1);
 allowed=0;reads=0;assert(wr_iot_rc_restart_guest_policy(&out)&&!out); /* enabled but outside schedule */
 enabled=0;allowed=1;reads=0;out=77;assert(!wr_iot_rc_restart_guest_policy(&out)&&out==77);allowed=0;
 for(int fault=0;fault<6;fault++){
  ap=fault==0;mode=fault==1?3:0;radio=fault==2?0:1;guard=fault!=3;enabled=fault==4?2:1;drift=fault==5;reads=0;out=77;
  assert(!wr_iot_rc_restart_guest_policy(&out)&&out==77);
 }
 ap=mode=0;radio=guard=1;enabled=1;out=77;assert(wr_iot_rc_restart_guest_isolation_policy(&out)&&out==1);enabled=2;out=77;assert(!wr_iot_rc_restart_guest_isolation_policy(&out)&&out==77);
 for(int fault=1;fault<=3;fault++){
  ap=mode=0;radio=guard=enabled=1;isolate_reads=0;mode_drift=fault;out=77;
  assert(!wr_iot_rc_restart_guest_isolation_policy(&out)&&out==77);
 }
 assert(!wr_iot_rc_restart_guest_policy(NULL));
 puts("PASS extracted SDK Guest policy adapter: OFF, enabled/scheduled ON, outside schedule OFF, unsupported mode/radio/AP/guard/value/drift refuse without output mutation; SDK reads injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-guest-policy-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
