from pathlib import Path
import subprocess,tempfile,json
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-entry-source-') as d:
 root=Path(d);rc=root/'trunk/user/rc';(rc/'wr-iot').mkdir(parents=True)
 (root/'iot-iapp-policy-source.json').write_text(json.dumps({'board':'WR1200JS','production_ready':False,'iapp_compile_gate_enabled':True}))
 (rc/'wr-iot/restart-iapp-policy.h').write_text('#define WR_IOT_IAPP_POLICY_PREPARED 1\n')
 (rc/'net_wifi.c').write_text('static int legacy;\nvoid\nrestart_wifi_rt(int radio_on, int need_reload_conf)\n{\n (void)radio_on;(void)need_reload_conf;legacy++;\n}\n')
 (rc/'wr-iot-rc-backend.c').write_text('enum {WR_IOT_OWNER_IDLE,WR_IOT_OWNER_INITIAL_OFF,OTHER};\nstatic struct {int phase,busy;}backend;static struct {int owner;}rebind;\n')
 (rc/'Makefile').write_text('OBJS=wr-iot-restart-scheduler.o\n')
 cmd=['python3','-B',str(here/'prepare-restart-entry-source.py'),str(root)]
 subprocess.run(cmd,check=True)
 subprocess.run(['python3','-B',str(here/'check-restart-entry-manifest.py'),str(root)],check=True)
 net=(rc/'net_wifi.c').read_text();back=(rc/'wr-iot-rc-backend.c').read_text()
 assert net.index('WR_IOT_PRIVATE_RESTART_ENTRY')<net.index('legacy++')
 code='#define BOARD_WR1200JS\n#include <assert.h>\nstatic int claimed;\nint wr_iot_restart_entry(int on,int reload){assert(on==1&&reload==1);return claimed;}\n'+net+back+r'''
int main(void){
 assert(!wr_iot_rc_restart_owned());backend.phase=WR_IOT_OWNER_INITIAL_OFF;assert(!wr_iot_rc_restart_owned());
 backend.phase=OTHER;assert(wr_iot_rc_restart_owned());backend.phase=WR_IOT_OWNER_IDLE;
 rebind.owner=1;assert(wr_iot_rc_restart_owned());rebind.owner=0;backend.busy=1;assert(wr_iot_rc_restart_owned());
 claimed=1;restart_wifi_rt(1,1);assert(!legacy);
 claimed=0;restart_wifi_rt(1,1);assert(legacy==1);
}
'''
 p=root/'test.c';p.write_text(code);b=root/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-I'+str(rc),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
 original=(rc/'net_wifi.c').read_text();(rc/'net_wifi.c').write_text(original+'// drift\n')
 assert subprocess.run(['python3','-B',str(here/'check-restart-entry-manifest.py'),str(root)],capture_output=True).returncode
 (rc/'net_wifi.c').write_text(original)
 before=(rc/'net_wifi.c').read_bytes();assert subprocess.run(cmd,capture_output=True).returncode and (rc/'net_wifi.c').read_bytes()==before
print('PASS prepared restart hook: claim returns before legacy body, never-opened versus owned predicate, duplicate installer refuses; SDK body/entry actors, full SDK compilation pending')
