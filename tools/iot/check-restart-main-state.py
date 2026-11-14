#!/usr/bin/env python3
"""Fixed Main read-only adapter and actual prepared profile generator wrapper."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
module=ast.parse((here/'prepare-rc.py').read_text())
helper=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets))
a=helper.index('int wr_iot_rc_restart_generate(');b=helper.index('\n}',a)+2
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdarg.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
static int socket_fail,ioctl_fail,close_fail,up,ioctls,closes;
static int fake_socket(int d,int t,int p){assert(d==AF_INET&&t==(SOCK_DGRAM|SOCK_CLOEXEC)&&!p);return socket_fail?-1:7;}
static int fake_ioctl(int fd,unsigned long cmd,...){assert(fd==7&&cmd==SIOCGIFFLAGS);va_list v;va_start(v,cmd);struct ifreq*r=va_arg(v,struct ifreq*);va_end(v);assert(!strcmp(r->ifr_name,"ra0"));ioctls++;r->ifr_flags=up?IFF_UP:0;return ioctl_fail?-1:0;}
static int fake_close(int fd){assert(fd==7);closes++;return close_fail?-1:0;}
#define socket fake_socket
#define ioctl fake_ioctl
#define close fake_close
#include "restart-main-state.c"
#undef socket
#undef ioctl
#undef close
static int generated,result;
static int gen_ralink_config_2g(int disabled){assert(!disabled);generated++;return result;}
'''+helper[a:b]+r'''
int main(void){
 assert(wr_iot_restart_main_down()&&ioctls==1&&closes==1);
 up=1;assert(!wr_iot_restart_main_down());up=0;
 socket_fail=1;int before=ioctls;assert(!wr_iot_restart_main_down()&&ioctls==before);socket_fail=0;
 ioctl_fail=1;assert(!wr_iot_restart_main_down());ioctl_fail=0;
 close_fail=1;assert(!wr_iot_restart_main_down());close_fail=0;
 assert(!generated&&wr_iot_rc_restart_generate(1)==-1&&!generated);
 result=9;assert(wr_iot_rc_restart_generate(0)==9&&generated==1);result=0;
 assert(wr_iot_rc_restart_generate(0)==0&&generated==2);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restart-main-state-') as d:
 unit=Path(d)/'check.c';binary=Path(d)/'check';unit.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS fixed ra0 administrative read: only SIOCGIFFLAGS, socket/ioctl/close/up refusal; actual prepared generator wrapper forwards0 once and exact result, rejects other input; no Main UP/RF proof')
