"""Exact constructed SDK rollback adapter, no radio/config commit."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'local':here}
for node in ast.parse((here/'prepare-rc.py').read_text()).body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helper' for t in node.targets):
  if 'helper' in ns and isinstance(node.value,ast.Constant):break
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<SDK helper>','exec'),ns)
assert ns['helper'].count((here/'radio-on-rollback-state-sdk.inc').read_text())==1
assert '#include "wr-iot/radio-on-rollback-state.h"' in ns['helper']
code=r'''
#include <assert.h>
#include <string.h>
#include "radio-on-rollback-state.h"
static int guard=1,ap,mode,down=1,value=1,writes,fail_write,post_drift,reads,mode_drift;
static int wr_iot_service_guard_dup(void){return guard?9:-1;}
static int close(int fd){assert(fd==9);return 0;}
static int get_ap_mode(void){return ap;}
static int get_mode_radio_rt(void){return mode;}
static int wr_iot_radio_recovery_down_observed(const struct wr_iot_physical_stop_request*r){assert(r->action==WR_STOP_RELEASE);reads++;if(mode_drift)mode=1;return down&&!(post_drift&&reads==2);}
static void mlme_state_rt(int v){assert(v==0);writes++;if(!fail_write)value=v;}
static int nvram_get_int(const char*k){assert(!strcmp(k,"mlme_radio_rt"));return value;}
#include "radio-on-rollback-state-sdk.inc"
int main(void){
 struct wr_iot_physical_stop_request r={.action=WR_STOP_RELEASE};
 guard=0;assert(!wr_iot_rc_radio_on_rollback_state(&r)&&!writes);guard=1;
 ap=1;assert(!wr_iot_rc_radio_on_rollback_state(&r)&&!writes);ap=0;
 mode=1;assert(!wr_iot_rc_radio_on_rollback_state(&r)&&!writes);mode=0;
 down=0;assert(!wr_iot_rc_radio_on_rollback_state(&r)&&!writes);down=1;
 assert(wr_iot_rc_radio_on_rollback_state(&r)&&writes==1&&!value);
 int before=writes;assert(wr_iot_rc_radio_on_rollback_current(&r)&&writes==before);
 value=1;assert(!wr_iot_rc_radio_on_rollback_current(&r)&&writes==before);
 value=1;fail_write=1;assert(!wr_iot_rc_radio_on_rollback_state(&r)&&writes==2&&value);fail_write=0;
 reads=0;post_drift=1;assert(!wr_iot_rc_radio_on_rollback_state(&r)&&writes==3&&!value);
 post_drift=0;mode_drift=1;assert(!wr_iot_rc_radio_on_rollback_current(&r)&&writes==3);mode_drift=mode=0;
 down=0;assert(!wr_iot_rc_radio_on_rollback_current(&r)&&writes==3);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-rollback-state-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS constructed SDK rollback state: guarded mode0 fresh DOWN before/after MLME0, failed write/post-drift uncertain, no saved radio/reload/flash/RF mutation; SDK actors injected')
