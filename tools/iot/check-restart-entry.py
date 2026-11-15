from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <time.h>
#include "rc-backend.h"
#include "rc-physical-stop.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int held,guard=1,mode_ok=1,drift,reads,entropy_ok=1,claimed=1,calls;
int wr_iot_service_guard_enter(int on){assert(on==1);if(!guard)return 0;held++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&held==1);held--;}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode*m){assert(held);reads++;*m=(struct wr_iot_rc_mode){1,1,drift&&reads==2?2:0};return mode_ok;}
static int entropy(void*b,unsigned n,unsigned f){assert(held&&n==32&&f==1);memset(b,7,n);return entropy_ok?32:15;}
#define WR_IOT_GETRANDOM(b,n,f) entropy(b,n,f)
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent*i,const struct wr_iot_control_request*r){assert(!held&&!wr_iot_rc_shutdown.active&&!r->request.enabled&&!r->request.password[0]&&r->created&&strlen(r->id)==32&&i->restart&&i->radio_on&&i->reload==1);calls++;return claimed;}
#include "restart-entry.c"
int main(void){
 assert(!wr_iot_restart_entry(0,1)&&!calls);assert(!wr_iot_restart_entry(1,2));
 guard=0;assert(!wr_iot_restart_entry(1,1));guard=1;
 entropy_ok=0;assert(!wr_iot_restart_entry(1,1)&&!held&&!calls);entropy_ok=1;
 drift=1;reads=0;assert(!wr_iot_restart_entry(1,1)&&!held&&!calls);drift=0;
 mode_ok=0;assert(!wr_iot_restart_entry(1,1));mode_ok=1;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_entry(1,1)&&!calls);wr_iot_rc_shutdown.pending=0;
 assert(wr_iot_restart_entry(1,1)&&calls==1&&!held);
 claimed=0;assert(!wr_iot_restart_entry(1,1)&&calls==2&&!held);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restart-entry-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS restart entry: guarded stable mode/entropy/time OFF envelope, guard released before physical admission, pending/invalid/drift/short-entropy refusal, claim propagated; physical/SDK actors, net_wifi hook pending')
