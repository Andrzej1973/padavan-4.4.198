from pathlib import Path
import tempfile,subprocess
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdarg.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <linux/sockios.h>
#include <net/if.h>
#include <errno.h>
#include <string.h>
#include "radio-off-bridge.h"
static int depth,guard=1,observed=1,attached=1,foreign,up,absent,del_fail,close_fail,deletes;
static unsigned selected;
static const char* names[]={"ra1","ra0","wds3","wds2","wds1","wds0","apcli0"};
int wr_iot_service_guard_enter(int on){assert(on==1&&!depth);if(!guard)return 0;depth=1;return 1;}
void wr_iot_service_guard_leave(int t){assert(t==1&&depth);depth=0;}
int wr_iot_radio_off_observed(const struct wr_iot_physical_stop_request*r){assert(depth&&r->action==WR_STOP_RELEASE);return observed;}
unsigned if_nametoindex(const char*n){assert(depth);if(!strcmp(n,"br0"))return 9;assert(!strcmp(n,names[selected]));if(absent){errno=ENODEV;return 0;}return selected+1;}
static ssize_t fake_readlink(const char*p,char*b,size_t n){char expected[96];snprintf(expected,sizeof(expected),"/sys/class/net/%s/master",names[selected]);assert(!strcmp(p,expected));if(!attached){errno=ENOENT;return -1;}const char*v=foreign?"../../br-other":"../../br0";assert(strlen(v)<n);memcpy(b,v,strlen(v));return strlen(v);}
static int fake_stat(const char*p,struct stat*s){assert(!strcmp(p,"/sys/class/net/br0/bridge"));memset(s,0,sizeof(*s));s->st_mode=S_IFDIR;return 0;}
static int fake_socket(int d,int t,int p){assert(d==AF_INET&&t==(SOCK_DGRAM|SOCK_CLOEXEC)&&!p);return 7;}
static int fake_ioctl(int fd,unsigned long op,...){assert(fd==7&&depth);va_list a;va_start(a,op);struct ifreq*r=va_arg(a,struct ifreq*);va_end(a);if(op==SIOCGIFFLAGS){assert(!strcmp(r->ifr_name,names[selected]));r->ifr_flags=up?IFF_UP:0;return 0;}assert(op==SIOCBRDELIF&&!strcmp(r->ifr_name,"br0")&&r->ifr_ifindex==(int)selected+1);deletes++;if(del_fail)return -1;attached=0;return 0;}
static int fake_close(int fd){assert(fd==7);return close_fail?-1:0;}
#define readlink fake_readlink
#define stat fake_stat
#define socket fake_socket
#define ioctl fake_ioctl
#define close fake_close
#include "radio-off-bridge.c"
int main(void){
 struct wr_iot_physical_stop_request r={.action=WR_STOP_RELEASE};
 assert(wr_iot_radio_off_bridge_detach(&r,7)==WR_OFF_BRIDGE_REFUSED&&!deletes);
 for(selected=0;selected<7;selected++){
  attached=1;assert(wr_iot_radio_off_bridge_detach(&r,selected)==WR_OFF_BRIDGE_DETACHED&&!depth&&!attached);
  int before=deletes;assert(wr_iot_radio_off_bridge_detach(&r,selected)==WR_OFF_BRIDGE_DETACHED&&deletes==before);
  absent=1;assert(wr_iot_radio_off_bridge_detach(&r,selected)==(selected==1?WR_OFF_BRIDGE_REFUSED:WR_OFF_BRIDGE_DETACHED));absent=0;
 }
 selected=0;attached=1;int before=deletes;
 foreign=1;assert(wr_iot_radio_off_bridge_detach(&r,0)==WR_OFF_BRIDGE_REFUSED&&deletes==before);foreign=0;
 up=1;assert(wr_iot_radio_off_bridge_detach(&r,0)==WR_OFF_BRIDGE_REFUSED&&deletes==before);up=0;
 guard=0;assert(wr_iot_radio_off_bridge_detach(&r,0)==WR_OFF_BRIDGE_REFUSED);guard=1;
 observed=0;assert(wr_iot_radio_off_bridge_detach(&r,0)==WR_OFF_BRIDGE_REFUSED);observed=1;
 del_fail=1;assert(wr_iot_radio_off_bridge_detach(&r,0)==WR_OFF_BRIDGE_UNCERTAIN&&!depth);del_fail=0;
 close_fail=1;assert(wr_iot_radio_off_bridge_detach(&r,0)==WR_OFF_BRIDGE_UNCERTAIN&&!depth);
}
'''
# Preserve struct stat while replacing the function name only.
code=code.replace('#define stat fake_stat','#define stat(p,s) fake_stat(p,s)')
code=code.replace('#include <string.h>','#include <string.h>\n#include <stdio.h>')
with tempfile.TemporaryDirectory(prefix='wr-off-bridge-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS fixed OFF bridge detach: seven names, DOWN/current guard, optional absence, already-detached read-only, foreign/up refusal, ioctl/close uncertainty; syscalls injected, unbound')
