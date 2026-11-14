"""Restore + actual Guest/services controllers; generation/Main/SDK actors injected."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-restart-guest-controller.py').read_text())
base=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
base=base.split('int main(void)',1)[0]
base=base.replace('wr_iot_restart_guest_up(void){ups++;return result;}', 'wr_iot_restart_guest_up(void){ups++;state=1;return result;}')
base=base.replace('wr_iot_restart_guest_down(void){downs++;return WR_RESTART_UP_UNCERTAIN;}', 'wr_iot_restart_guest_down(void){downs++;state=0;return WR_RESTART_UP_UNCERTAIN;}')
code=base+r'''
#include "restart-services.h"
static int service_calls,main_ups;
int wr_iot_rc_restart_service_policy(struct wr_iot_restart_service_policy*p){*p=(struct wr_iot_restart_service_policy){0,-75,-80};return 1;}
enum wr_iot_restart_service_result wr_iot_rc_restart_service_submit(const struct wr_iot_restart_service_policy*p,unsigned slot){assert(p->kick_rssi==-75&&slot==(unsigned)service_calls);service_calls++;return WR_SERVICE_RETURNED;}
#include "restart-services.c"
int wr_iot_restart_generation_begin(struct wr_iot_restart_generation*g){g->owner=getpid();return 1;}
int wr_iot_restart_generation_step(struct wr_iot_restart_generation*g){assert(g->owner==getpid());return 1;}
int wr_iot_restart_main_begin(struct wr_iot_restart_main*m,struct wr_iot_restart_generation*g,const unsigned char*id){assert(id[0]);main_ups++;m->owner=getpid();m->generation=g;return 0;}
int wr_iot_rc_rebind_begin(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p){(void)r;(void)p;return 0;}
int wr_iot_rc_rebind_active_current(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i){(void)r;(void)p;(void)i;return 0;}
int wr_iot_restart_generation_origin_current(const struct wr_iot_restart_generation*g){return g->owner==getpid();}
#include "restart-restore.c"
int main(void){
 struct wr_iot_restart_restore s={0};unsigned char id[16]={7};wr_iot_rc_shutdown.active=1;
 result=WR_RESTART_UP_UNCERTAIN;
 assert(wr_iot_restart_restore_begin(&s,id));
 int prepared=0;
 for(int i=0;i<25&&!prepared;i++)prepared=wr_iot_restart_restore_step(&s);
 assert(prepared&&s.phase==WR_RESTORE_PREPARED&&main_ups==1&&ups==1&&adds==1&&service_calls==3);
 assert(s.guest.main==&s.main&&s.services.main==&s.main&&s.main.generation==&s.generation);
 wr_iot_rc_shutdown.pending=SIGTERM;
 assert(!wr_iot_restart_restore_step(&s)&&downs==1&&!state&&s.guest.phase==WR_GUEST_DOWN_OBSERVED);
 assert(!wr_iot_restart_restore_step(&s)&&downs==1&&service_calls==3);
 wr_iot_rc_shutdown.pending=0;
 assert(!wr_iot_restart_restore_step(&s)&&downs==1&&ups==1&&main_ups==1&&service_calls==3);
 puts("PASS restore/actual Guest/services controllers: ordered preparation, stable references, uncertain Guest UP reconciled, pending delegated to one DOWN, no resume/replay afterward; generation/Main/SDK/transport actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restore-compose-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
