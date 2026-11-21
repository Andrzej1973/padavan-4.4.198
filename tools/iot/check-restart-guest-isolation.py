from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
static char path[1024];static int up,foreign,guard=1;
#define WR_IOT_GUEST_ISOLATE_PATH path
int wr_iot_service_guard_dup(void){return guard?open("/dev/null",O_RDONLY):-1;}
int wr_iot_restart_guest_admin_state(int*out){*out=up;return 1;}
static ssize_t link_mock(const char*p,char*b,size_t n){assert(!strcmp(p,"/sys/class/net/ra1/master"));const char*s=foreign?"../../br-iot":"../../br0";assert(n>strlen(s));memcpy(b,s,strlen(s));return strlen(s);}
#define readlink link_mock
#include "restart-guest-isolation.c"
int main(int argc,char**argv){
 assert(argc==2);snprintf(path,sizeof(path),"%s/isolate",argv[1]);
 assert(wr_iot_restart_guest_isolation_prepare(1));up=1;assert(wr_iot_restart_guest_isolation_current(1));assert(!wr_iot_restart_guest_isolation_current(0));up=0;assert(wr_iot_restart_guest_isolation_prepare(0));
 up=1;assert(!wr_iot_restart_guest_isolation_prepare(1));up=0;
 foreign=1;assert(!wr_iot_restart_guest_isolation_prepare(1));foreign=0;
 guard=0;assert(!wr_iot_restart_guest_isolation_prepare(1));guard=1;
 assert(!wr_iot_restart_guest_isolation_prepare(2));assert(!unlink(path));
 puts("PASS Guest isolate_mode adapter: write/read0/1 under guard while ra1 DOWN/master br0, UP/foreign master/guard/value refusal; sysfs regular-file fixture, not kernel/firewall acceptance");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-guest-isolation-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True)
