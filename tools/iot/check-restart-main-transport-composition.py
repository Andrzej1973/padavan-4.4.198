"""Actual generation/Main controller/UP transport; kernel calls injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-main-composition.py').read_text();ns={'__file__':str(here/'check-restart-main-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<actual composition setup>','exec'),ns)
body=ns['body']
old='enum wr_iot_restart_up_result wr_iot_restart_main_up(void){ups++;main_down=0;return WR_RESTART_UP_UNCERTAIN;}'
assert body.count(old)==1
new=r'''
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <stdarg.h>
static int transport_socket(int domain,int type,int protocol){assert(domain==AF_INET&&type==(SOCK_DGRAM|SOCK_CLOEXEC)&&!protocol);return 77;}
static int transport_ioctl(int fd,unsigned long operation,...){
 assert(fd==77);va_list args;va_start(args,operation);struct ifreq*r=va_arg(args,struct ifreq*);va_end(args);
 assert(!strcmp(r->ifr_name,"ra0"));
 if(operation==SIOCGIFFLAGS){r->ifr_flags=IFF_BROADCAST;return 0;}
 assert(operation==SIOCSIFFLAGS&&r->ifr_flags==(IFF_UP|IFF_BROADCAST));ups++;main_down=0;
 return -1; /* May follow actual ndo_open despite userspace error. */
}
static int transport_close(int fd){assert(fd==77);return 0;}
#define socket transport_socket
#define ioctl transport_ioctl
#define close transport_close
#include "restart-main-up.c"
#undef socket
#undef ioctl
#undef close
'''
body=body.replace(old,new).replace('PASS actual generation/profile journal/Main controller:', 'PASS actual generation/profile journal/Main controller/UP transport:')
with tempfile.TemporaryDirectory(prefix='wr-main-transport-compose-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n');unit=root/'check.c';unit.write_text(body);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary),d],check=True)
