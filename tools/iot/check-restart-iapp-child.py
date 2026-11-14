"""Real fork/pipe/exec with PID1-like SIGCHLD reaper and fixed script fixture."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include "restart-iapp-child.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int guard=1;
int wr_iot_service_guard_dup(void){return guard?dup(1):-1;}
static void reap(int sig){(void)sig;while(waitpid(-1,0,WNOHANG)>0){}}
int main(void){
 struct sigaction a={0};a.sa_handler=reap;sigemptyset(&a.sa_mask);assert(!sigaction(SIGCHLD,&a,0));
 int leak[2];assert(!pipe2(leak,O_NONBLOCK));
 struct wr_iot_iapp_child s={0};assert(wr_iot_iapp_child_closed(&s));
 assert(!wr_iot_iapp_child_begin(&s)&&!s.owner);
 wr_iot_rc_shutdown.active=1;guard=0;assert(!wr_iot_iapp_child_begin(&s)&&!s.owner);guard=1;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_iapp_child_begin(&s)&&!s.owner);wr_iot_rc_shutdown.pending=0;
 assert(wr_iot_iapp_child_begin(&s)&&!wr_iot_iapp_child_closed(&s));
 guard=0;assert(!wr_iot_iapp_child_step(&s));guard=1;
 wr_iot_rc_shutdown.pending=SIGTERM;
 close(leak[1]);char unused;int eof=0;
 for(int i=0;i<200&&!eof;i++){int n=read(leak[0],&unused,1);if(n==0)eof=1;else{assert(n<0&&errno==EAGAIN);usleep(10000);}}
 assert(eof);close(leak[0]);
 if(EXPECTED_PENDING)assert(wr_iot_iapp_child_step(&s)==0);
 assert(!wr_iot_iapp_child_begin(&s));int result=0;
 for(int i=0;i<200&&!result;i++){result=wr_iot_iapp_child_step(&s);if(!result)usleep(10000);}
 assert(result==EXPECTED&&s.fd==-1&&wr_iot_iapp_child_step(&s)==EXPECTED&&wr_iot_iapp_child_closed(&s));
 int lost[2];assert(!pipe2(lost,O_NONBLOCK));close(lost[1]);
 struct wr_iot_iapp_child unknown={.owner=getpid(),.attempted=1,.fd=lost[0]};
 assert(wr_iot_iapp_child_step(&unknown)==-2&&!wr_iot_iapp_child_closed(&unknown));
 assert(wr_iot_iapp_child_step(&unknown)==-2&&!wr_iot_iapp_child_begin(&unknown));
 int invalid[2];assert(!pipe2(invalid,O_NONBLOCK));unsigned char bad=9;assert(write(invalid[1],&bad,1)==1);close(invalid[1]);
 unknown=(struct wr_iot_iapp_child){.owner=getpid(),.attempted=1,.fd=invalid[0]};
 assert(wr_iot_iapp_child_step(&unknown)==-2&&!wr_iot_iapp_child_closed(&unknown));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iapp-child-') as d:
 root=Path(d);script=root/'iappd.sh';p=root/'test.c';p.write_text(code)
 for status in (0,7,127):
  script.write_text('#!/bin/sh\n[ "$1" = restart ] || exit 99\nsleep 1\nexit '+str(status)+'\n');script.chmod(0o700)
  if status==127:script.unlink()
  b=root/'test'
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),'-DWR_IOT_IAPP_SCRIPT="'+str(script)+'"','-DEXPECTED='+('1' if status==0 else '-1'),'-DEXPECTED_PENDING='+('0' if status==127 else '1'),str(p),str(here/'restart-iapp-child.c'),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True,timeout=5)
print('PASS actual IAPP child supervisor/pipe/exec: PID1-style reaper cannot steal script receipt, exit0/nonzero distinguished, nonblocking parent polling, duplicate begin refuses; fixture script only, ownership/root binding pending')
