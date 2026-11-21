from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <time.h>
#include "rc-backend.h"
#include "rc-physical-stop.h"
#include "rc-shutdown-admission.h"
#include "restart-entry.h"
enum wr_iot_radio_entry_result wr_iot_cold_on_entry(int on,int reload){(void)on;(void)reload;return WR_RADIO_ENTRY_NATIVE;}
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int owned=1;
int wr_iot_rc_restart_owned(void){return owned;}
static int held,guard=1,mode_ok=1,drift,reads,entropy_ok=1,claimed=1,calls,clock_fault,zero_entropy;
int wr_iot_service_guard_enter(int on){assert(on==1);if(!guard)return 0;held++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&held==1);held--;}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode*m){assert(held);reads++;*m=(struct wr_iot_rc_mode){1,1,drift&&reads==2?2:0};return mode_ok;}
static int entropy(void*b,unsigned n,unsigned f){assert(held&&n==32&&f==1);memset(b,zero_entropy?0:7,n);return entropy_ok?32:15;}
#define WR_IOT_GETRANDOM(b,n,f) entropy(b,n,f)
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent*i,const struct wr_iot_control_request*r){assert(!held&&!wr_iot_rc_shutdown.active&&!r->request.enabled&&!r->request.password[0]&&r->created&&strlen(r->id)==32&&i->restart&&i->radio_on&&i->reload==1);calls++;return claimed;}
int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request*r){(void)r;return 0;}
int wr_iot_rc_radio_on_saved_request(struct wr_iot_request*r){(void)r;assert(0);return 0;}
int wr_iot_rc_radio_on_begin(const struct wr_iot_control_request*r,int reload){(void)r;(void)reload;assert(0);return 0;}
int wr_iot_rc_radio_off_begin(const struct wr_iot_control_request*r,int reload){(void)r;(void)reload;assert(0);return 0;}
static int entry_clock(clockid_t id,struct timespec*out){assert(held&&id==CLOCK_MONOTONIC);if(clock_fault)return -1;out->tv_sec=10;out->tv_nsec=0;return 0;}
#define clock_gettime entry_clock
#include "restart-entry.c"
int main(void){
 wr_iot_rc_shutdown.radio_on_owned=1;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!reads&&!calls&&!held);wr_iot_rc_shutdown.radio_on_owned=0;
 wr_iot_rc_shutdown.radio_off_owned=1;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!reads&&!calls&&!held);wr_iot_rc_shutdown.radio_off_owned=0;
 owned=0;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_NATIVE&&!calls);owned=1;
 assert(wr_iot_restart_entry(0,1)==WR_RADIO_ENTRY_NATIVE&&!calls);assert(wr_iot_restart_entry(1,2)==WR_RADIO_ENTRY_REFUSED);
 guard=0;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED);guard=1;
 entropy_ok=0;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!held&&!calls);entropy_ok=1;
 drift=1;reads=0;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!held&&!calls);drift=0;
 mode_ok=0;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED);mode_ok=1;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!calls);wr_iot_rc_shutdown.pending=0;
 assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_OWNED&&calls==1&&!held);
 claimed=0;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&calls==2&&!held);
}
'''
tree=ast.parse((here/'prepare-restart-entry-source.py').read_text())
hook=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
wrapper=r'''
#define BOARD_WR1200JS 1
#define WR_IOT_IAPP_POLICY_PREPARED 1
static int legacy_calls,legacy_bug_calls;
enum wr_iot_radio_entry_result wr_iot_initial_restart_entry(int on,int reload){(void)on;(void)reload;return WR_RADIO_ENTRY_NATIVE;}
static void generated_restart(int radio_on,int need_reload_conf){
'''+hook+r'''
 legacy_calls++;
}
static void predecessor_restart(int radio_on,int need_reload_conf){
'''+hook.replace('if(wr_iot_restart_entry(radio_on,need_reload_conf)!=WR_RADIO_ENTRY_NATIVE)return;',
                 'if(wr_iot_restart_entry(radio_on,need_reload_conf)==WR_RADIO_ENTRY_OWNED)return;')+r'''
 legacy_bug_calls++;
}
'''
code=code.replace('int main(void){',wrapper+'\nint main(void){',1)
anchor=' claimed=0;assert(wr_iot_restart_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&calls==2&&!held);'
assert code.count(anchor)==1
code=code.replace(anchor,anchor+r'''
 /* Execute the exact generated caller with the actual entry implementation. */
 calls=0;claimed=1;reads=0;
 guard=0;generated_restart(1,1);assert(!legacy_calls&&!calls);guard=1;
 clock_fault=1;generated_restart(1,1);assert(!legacy_calls&&!calls);clock_fault=0;
 entropy_ok=0;generated_restart(1,1);assert(!legacy_calls&&!calls);
 predecessor_restart(1,1);assert(legacy_bug_calls==1&&!calls); /* Old boolean refusal falls through. */
 entropy_ok=1;zero_entropy=1;generated_restart(1,1);assert(!legacy_calls&&!calls);zero_entropy=0;
 mode_ok=0;generated_restart(1,1);assert(!legacy_calls&&!calls);mode_ok=1;
 drift=1;reads=0;generated_restart(1,1);assert(!legacy_calls&&!calls);drift=0;
 wr_iot_rc_shutdown.pending=SIGTERM;generated_restart(1,1);assert(!legacy_calls&&!calls);wr_iot_rc_shutdown.pending=0;
 claimed=0;generated_restart(1,1);assert(!legacy_calls&&calls==1);claimed=1;
 generated_restart(1,1);assert(!legacy_calls&&calls==2&&!held);
 owned=0;generated_restart(1,1);assert(legacy_calls==1&&calls==2&&!held);
''')

with tempfile.TemporaryDirectory(prefix='wr-restart-entry-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS restart entry: guarded stable mode/entropy/time OFF envelope, guard released before physical admission, pending/invalid/drift/short-entropy refusal, claim propagated; actual generated caller + real entry refuse without legacy fallback; predecessor boolean defect reproduced; physical/SDK actors, no target/runtime claim')
