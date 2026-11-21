"""Non-sleeping SDK authentication-stop controller; service adapters injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <signal.h>
#include "restart-auth-stop.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int present=1,signals,ok=1;
int wr_iot_auth_stop_present(void){return present;}
int wr_iot_auth_stop_signal(int sig){assert(sig==(signals?SIGKILL:SIGTERM));signals++;return ok;}
int main(void){
 struct wr_iot_auth_stop s={0};assert(!wr_iot_auth_stop_begin(&s,10));
 wr_iot_rc_shutdown.active=1;assert(wr_iot_auth_stop_begin(&s,10)&&signals==1);
 assert(!wr_iot_auth_stop_begin(&s,11));assert(!wr_iot_auth_stop_step(&s,9));
 assert(!wr_iot_auth_stop_step(&s,3009)&&signals==1);
 assert(!wr_iot_auth_stop_step(&s,3010)&&signals==2&&s.attempted==3);
 assert(!wr_iot_auth_stop_step(&s,4010)&&s.phase==WR_AUTH_RETAINED);
 present=0;assert(!wr_iot_auth_stop_step(&s,4011)&&signals==2);
 s=(struct wr_iot_auth_stop){0};assert(wr_iot_auth_stop_begin(&s,5000));
 assert(wr_iot_auth_stop_step(&s,5001)&&s.phase==WR_AUTH_STOPPED);
 present=1;assert(!wr_iot_auth_stop_step(&s,5002)&&s.phase==WR_AUTH_RETAINED);
 s=(struct wr_iot_auth_stop){0};signals=0;ok=0;
 assert(wr_iot_auth_stop_begin(&s,6000)&&s.phase==WR_AUTH_RETAINED&&signals==1);
 assert(!wr_iot_auth_stop_step(&s,9999)&&signals==1);
 s=(struct wr_iot_auth_stop){0};present=-1;assert(wr_iot_auth_stop_begin(&s,10000)&&s.phase==WR_AUTH_RETAINED);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-auth-stop-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'restart-auth-stop.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS non-sleeping auth stop: TERM once,3s deadline,KILL once,1s observation, clock reversal/unknown/uncertain/foreign return retain, absence rechecked; service actors injected, SDK binding pending')
