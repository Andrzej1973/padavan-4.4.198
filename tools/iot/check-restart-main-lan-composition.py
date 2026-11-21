"""Actual Main controller and bridge transport with kernel boundary injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
def literal(name,var):
 tree=ast.parse((here/name).read_text())
 return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==var for t in n.targets))
controller=literal('check-restart-main-controller.py','code').split('int main(void)',1)[0]
controller=controller.replace('enum wr_iot_main_bridge_result wr_iot_restart_main_bridge_attach(void){assert(0);return WR_MAIN_BRIDGE_REFUSED;}','').replace('int wr_iot_restart_main_bridge_current(void){assert(0);return 0;}','')
bridge=literal('check-restart-main-bridge.py','code').split('int main(void)',1)[0]
bridge=bridge.replace('int wr_iot_service_guard_dup(void){return guard_ok?88:-1;}','')
bridge=bridge.replace('static int f_close(int fd){assert(fd==88||fd==99);return fd==99&&close_fail?-1:0;}', 'static int f_close(int fd){if(fd!=99)return close(fd);return close_fail?-1:0;}')
bridge=bridge.replace(',guard_ok=1','')
# Compile actual adapter before controller; restrict syscall macros to adapter.
a=controller.index('#include "restart-main-controller.c"')
code=controller[:a]+bridge+'\n#undef close\n#undef socket\n#undef if_nametoindex\n#undef stat\n#undef readlink\n#undef ioctl\n'+controller[a:]+r'''
int main(void){
 struct wr_iot_restart_generation g={.owner=getpid(),.phase=WR_RESTART_GEN_VERIFIED,.profile={.active=1},.origin={.physical={.epoch=1,.generation=3}}};
 struct wr_iot_restart_main s={0};unsigned char id[16]={7};wr_iot_rc_shutdown.active=1;outcome=WR_RESTART_UP_RETURNED;
 assert(wr_iot_restart_main_begin(&s,&g,id));
 probe_ok=0;assert(!wr_iot_restart_main_lan_step(&s)&&!adds);probe_ok=1;
 add_fail=1;assert(wr_iot_restart_main_lan_step(&s)&&adds==1&&s.bridge_attempted); /* ioctl error but confirmed membership. */
 assert(wr_iot_restart_main_lan_step(&s)&&adds==1&&calls==1);
 current_master=0;assert(!wr_iot_restart_main_lan_step(&s)&&adds==1); /* Lost membership cannot replay add. */
 current_master=2;assert(!wr_iot_restart_main_lan_step(&s)&&adds==1);
 current_master=1;epoch=3;assert(!wr_iot_restart_main_lan_step(&s)&&adds==1);epoch=2;
 assert(wr_iot_restart_main_lan_step(&s)&&g.profile.active&&g.main_may_have_started);
 puts("PASS actual Main controller/bridge transport: ioctl error reconciled by exact membership, one add, detached/foreign master never replayed, epoch gate before mutation; driver/generation and bridge syscalls injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-main-lan-compose-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
