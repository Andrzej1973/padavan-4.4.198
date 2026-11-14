"""Actual fixed SDK auth adapter + actual asynchronous controller."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <signal.h>
#include <string.h>
#include "restart-auth-stop.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int guard=1,ap,mode,running=1,signals,fail;
static int wr_iot_service_guard_dup(void){return guard?9:-1;}
static int close(int fd){assert(fd==9);return 0;}
static int get_ap_mode(void){return ap;}
static int get_mode_radio_rt(void){return mode;}
static int pids(const char*n){assert(!strcmp(n,"rtinicapd"));return running;}
static int doSystem(const char*f,const char*a,const char*b){assert(!strcmp(f,"killall %s %s")&&!strcmp(b,"rtinicapd"));assert(!strcmp(a,signals?"-SIGKILL":"-q"));signals++;return fail;}
#include "restart-auth-stop-sdk.inc"
int main(void){
 assert(!wr_iot_auth_stop_signal(SIGUSR1)&&!signals);
 guard=0;assert(wr_iot_auth_stop_present()==-1&&!wr_iot_auth_stop_signal(SIGTERM));guard=1;
 ap=1;assert(wr_iot_auth_stop_present()==-1);ap=0;mode=2;assert(!wr_iot_auth_stop_signal(SIGTERM));mode=0;
 running=-1;assert(wr_iot_auth_stop_present()==-1);running=0;
 assert(wr_iot_auth_stop_signal(SIGTERM)&&!signals);
 running=1;wr_iot_rc_shutdown.active=1;struct wr_iot_auth_stop s={0};
 assert(wr_iot_auth_stop_begin(&s,100)&&signals==1);
 assert(!wr_iot_auth_stop_step(&s,3099)&&signals==1);
 assert(!wr_iot_auth_stop_step(&s,3100)&&signals==2);
 running=0;assert(wr_iot_auth_stop_step(&s,3101));
 running=1;assert(!wr_iot_auth_stop_step(&s,3102)&&s.phase==WR_AUTH_RETAINED);
 s=(struct wr_iot_auth_stop){0};signals=0;fail=1;
 assert(wr_iot_auth_stop_begin(&s,4000)&&signals==1&&s.phase==WR_AUTH_RETAINED);
 assert(!wr_iot_auth_stop_step(&s,8000)&&signals==1);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-auth-sdk-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'restart-auth-stop.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual auth SDK adapter/controller: guard/mode/presence gates, fixed TERM/KILL commands, no sleeps, deadlines/one attempt/absence drift/uncertain retention; SDK process/command actors injected')
