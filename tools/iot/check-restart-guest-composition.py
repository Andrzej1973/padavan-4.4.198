"""Guest controller + actual DOWN bridge and isolate adapter; kernel injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
def literal(file,var):
 tree=ast.parse((here/file).read_text())
 return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==var for t in n.targets))
bridge=literal('check-restart-guest-bridge.py','code').split('int main(void)',1)[0]
# System calls mocked solely for bridge object; sysfs isolate file is real.
code=bridge+r'''
#undef close
#undef socket
#undef if_nametoindex
#undef stat
#undef ioctl
#undef readlink
static char isolate_path[1024];
#define WR_IOT_GUEST_ISOLATE_PATH isolate_path
#define readlink f_link
'''
# Adjust the shared readlink mock for both interfaces' master paths.
code=code.replace('assert(!strcmp(p,"/sys/class/net/ra1/master"))','assert(!strcmp(p,"/sys/class/net/ra1/master"))')
# Bridge fixture guard returns88; isolate close must use same close mock.
code+=r'''
#define close f_close
#include "restart-guest-isolation.c"
#undef close
#undef readlink
#include "restart-guest-controller.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int ups,downs,desired=1;
int wr_iot_restart_main_lan_step(struct wr_iot_restart_main*m){assert(m);return 1;}
int wr_iot_rc_restart_guest_policy(int*out){*out=desired;return 1;}
int wr_iot_rc_restart_guest_isolation_policy(int*out){*out=1;return 1;}
enum wr_iot_restart_up_result wr_iot_restart_guest_up(void){assert(!up&&current_master==1&&wr_iot_restart_guest_isolation_current(1));ups++;up=1;return WR_RESTART_UP_UNCERTAIN;}
enum wr_iot_restart_up_result wr_iot_restart_guest_down(void){downs++;up=0;return WR_RESTART_UP_UNCERTAIN;}
#include "restart-guest-controller.c"
int main(int argc,char**argv){
 assert(argc==2);snprintf(isolate_path,sizeof(isolate_path),"%s/isolate",argv[1]);
 wr_iot_rc_shutdown.active=1;struct wr_iot_restart_main main={0};struct wr_iot_restart_guest guest={0};
 assert(wr_iot_restart_guest_begin(&guest,&main)&&!up&&!adds);
 assert(!wr_iot_restart_guest_step(&guest)&&guest.phase==WR_GUEST_ISOLATE&&current_master==1&&adds==1&&!up);
 assert(!wr_iot_restart_guest_step(&guest)&&guest.phase==WR_GUEST_OPEN&&!up&&wr_iot_restart_guest_isolation_current(1));
 assert(!wr_iot_restart_guest_step(&guest)&&up&&ups==1&&guest.phase==WR_GUEST_WAIT);
 assert(wr_iot_restart_guest_step(&guest)&&guest.phase==WR_GUEST_ADMIN_UP&&ups==1&&adds==1);
 FILE*f=fopen(isolate_path,"w");assert(f&&fputs("0\n",f)>=0&&!fclose(f));
 assert(!wr_iot_restart_guest_step(&guest)&&ups==1&&adds==1); /* No unsafe isolation rewrite after UP. */
 assert(!up&&downs==1&&guest.phase==WR_GUEST_DOWN_OBSERVED);
 assert(!wr_iot_restart_guest_step(&guest)&&downs==1&&ups==1);
 assert(!unlink(isolate_path));
 puts("PASS actual Guest controller/DOWN bridge/isolate composition: bridge before isolation before UP, post-UP isolation loss triggers one DOWN, observed without reopening; bridge syscalls/Main/policy/UP injected, real file IO; routed firewall not verified");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-guest-compose-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True)
