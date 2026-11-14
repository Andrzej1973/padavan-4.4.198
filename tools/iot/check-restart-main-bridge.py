from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <stdarg.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <linux/sockios.h>
#include <net/if.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
static int current_master,up=1,adds,socket_fail,add_fail,close_fail,guard_ok=1,missing,not_bridge;
int wr_iot_service_guard_dup(void){return guard_ok?88:-1;}
static int f_close(int fd){assert(fd==88||fd==99);return fd==99&&close_fail?-1:0;}
static int f_socket(int d,int t,int p){assert(d==AF_INET&&t==(SOCK_DGRAM|SOCK_CLOEXEC)&&!p);return socket_fail?-1:99;}
static unsigned f_index(const char*n){assert(!strcmp(n,"ra0")||!strcmp(n,"br0"));return missing?0:!strcmp(n,"ra0")?7:8;}
static int f_stat(const char*p,struct stat*s){assert(!strcmp(p,"/sys/class/net/br0/bridge"));s->st_mode=not_bridge?S_IFREG:S_IFDIR;return 0;}
static ssize_t f_link(const char*p,char*b,size_t n){assert(!strcmp(p,"/sys/class/net/ra0/master"));if(!current_master){errno=ENOENT;return -1;}const char*t=current_master==1?"../../br0":"../../br-iot";assert(strlen(t)<n);memcpy(b,t,strlen(t));return strlen(t);}
static int f_ioctl(int fd,unsigned long op,...){assert(fd==99);va_list a;va_start(a,op);struct ifreq*r=va_arg(a,struct ifreq*);va_end(a);
 if(op==SIOCGIFFLAGS){assert(!strcmp(r->ifr_name,"ra0"));r->ifr_flags=up?IFF_UP:0;return 0;}
 assert(op==SIOCBRADDIF&&!strcmp(r->ifr_name,"br0")&&r->ifr_ifindex==7);adds++;current_master=1;return add_fail?-1:0;
}
#define close f_close
#define socket f_socket
#define if_nametoindex f_index
/* Function-like macro preserves struct stat declarations. */
#define stat(p,s) f_stat(p,s)
#define readlink f_link
#define ioctl f_ioctl
#include "restart-main-bridge.c"
int main(void){
 assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_ATTACHED&&adds==1);
 assert(wr_iot_restart_main_bridge_current());assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_ATTACHED&&adds==1);
 current_master=2;assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_REFUSED&&adds==1);current_master=0;
 up=0;assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_REFUSED&&adds==1);up=1;
 guard_ok=0;assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_REFUSED);guard_ok=1;
 missing=1;assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_REFUSED);missing=0;
 not_bridge=1;assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_REFUSED);not_bridge=0;
 socket_fail=1;assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_REFUSED);socket_fail=0;
 add_fail=1;assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_UNCERTAIN&&adds==2);add_fail=0;assert(wr_iot_restart_main_bridge_current());
 current_master=0;close_fail=1;assert(wr_iot_restart_main_bridge_attach()==WR_MAIN_BRIDGE_UNCERTAIN&&adds==3);
 puts("PASS exact ra0/br0 bridge adapter: readback membership, no duplicate add, foreign master refused, UP/guard/index/bridge checks, ioctl/close uncertainty; syscalls injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-main-bridge-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
