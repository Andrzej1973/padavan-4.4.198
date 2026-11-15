from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include "rc-backend.h"
static int present=1,up,foreign,drift,reads,calls,mode,guard=1,absent_error=ENODEV;
int wr_iot_service_guard_dup(void){return guard?88:-1;}
int wr_iot_rc_mode_read(struct wr_iot_rc_mode*m){m->router=m->radio=1;m->mode=mode;return 1;}
static int f_close(int fd){assert(fd==88||fd==99);return 0;}
static int f_socket(int a,int b,int c){assert(a==AF_INET&&(b&SOCK_DGRAM)&&!c);return 99;}
static unsigned f_index(const char*n){assert(!strcmp(n,"wds3")||!strcmp(n,"wds2")||!strcmp(n,"wds1")||!strcmp(n,"wds0")||!strcmp(n,"apcli0"));reads++;if(!present){errno=absent_error;return 0;}return drift&&reads==2?11:10;}
static int f_ioctl(int fd,unsigned long op,struct ifreq*r){assert(fd==99&&op==SIOCGIFFLAGS);calls++;r->ifr_flags=up?IFF_UP:0;return 0;}
static ssize_t f_readlink(const char*path,char*b,size_t n){assert(strstr(path,"/sys/class/net/")&&strstr(path,"/master")&&n==1);if(foreign){*b='x';return 1;}errno=ENOENT;return -1;}
#define close f_close
#define socket f_socket
#define ioctl f_ioctl
#define if_nametoindex f_index
#define readlink f_readlink
#include "radio-on-aux.c"
int main(void){
 assert(wr_iot_on_aux_down_current()&&calls==5);
 up=1;assert(!wr_iot_on_aux_down_current());up=0;
 foreign=1;assert(!wr_iot_on_aux_down_current());foreign=0;
 drift=1;reads=0;assert(!wr_iot_on_aux_down_current());drift=0;
 mode=1;assert(!wr_iot_on_aux_down_current());mode=0;
 present=0;calls=0;assert(wr_iot_on_aux_down_current()&&!calls);
 absent_error=ENXIO;assert(wr_iot_on_aux_down_current());absent_error=EPERM;assert(!wr_iot_on_aux_down_current());
 guard=0;assert(!wr_iot_on_aux_down_current());
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-aux-') as d:
    p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b)],check=True,timeout=15)
print('PASS ON mode0 AUX observation: five fixed WDS/APCLI DOWN/detached, missing only ENODEV/ENXIO, UP/master/ifindex/mode/guard refusal, no mutation; syscalls injected')
