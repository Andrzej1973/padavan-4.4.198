from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''#include <assert.h>
#include <stdio.h>
#include <unistd.h>
#include "restart-restore.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int phase,ups,main_ok=1,guest_ok=1,services_ok=1,guest_calls;
int wr_iot_restart_generation_begin(struct wr_iot_restart_generation*g){assert(!phase);phase=1;g->owner=getpid();g->origin.desired.enabled=1;return 1;}
int wr_iot_restart_generation_step(struct wr_iot_restart_generation*g){assert(g->owner==getpid()&&phase==1);phase=2;return 1;}
int wr_iot_restart_main_begin(struct wr_iot_restart_main*m,struct wr_iot_restart_generation*g,const unsigned char*id){assert(phase==2&&id[0]&&g->owner==getpid());phase=3;ups++;m->owner=getpid();m->generation=g;g->main_may_have_started=1;return 0;}
int wr_iot_restart_main_lan_step(struct wr_iot_restart_main*m){assert(m->generation);return main_ok;}
int wr_iot_restart_guest_begin(struct wr_iot_restart_guest*g,struct wr_iot_restart_main*m){assert(phase==3&&m->owner==getpid());phase=4;g->owner=getpid();g->main=m;return 1;}
int wr_iot_restart_guest_step(struct wr_iot_restart_guest*g){assert(g->main);guest_calls++;return guest_ok;}
int wr_iot_restart_services_begin(struct wr_iot_restart_services*s,struct wr_iot_restart_main*m){assert(phase==4);phase=5;s->owner=getpid();s->main=m;return 1;}
int wr_iot_restart_services_step(struct wr_iot_restart_services*s){assert(s->main);return services_ok;}
static int rebind_calls;
int wr_iot_rc_rebind_begin(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p){assert(r->created==10&&p);rebind_calls++;return 0;}
static int active_ok,active_reads;
int wr_iot_rc_rebind_active_current(const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p,const struct wr_iot_driver_identity*i){assert(r->created==10&&!strcmp(r->id,"01000000000000000000000000000000")&&r->request.enabled==1&&p&&i);active_reads++;return active_ok;}
int wr_iot_restart_generation_origin_current(const struct wr_iot_restart_generation*g){return g->owner==getpid();}
int wr_iot_restart_generation_abort(struct wr_iot_restart_generation*g){(void)g;return 0;}
#include "check-multicast-owner-actor.h"
#include "restart-restore.c"
int main(void){
 struct wr_iot_restart_restore s={0};unsigned char id[16]={1};wr_iot_rc_shutdown.active=1;
 assert(wr_iot_restart_restore_begin(&s,id));assert(!wr_iot_restart_restore_begin(&s,id));
 assert(!wr_iot_restart_restore_step(&s));assert(!wr_iot_restart_restore_step(&s)&&ups==1);
 main_ok=0;assert(!wr_iot_restart_restore_step(&s)&&ups==1);main_ok=1;
 assert(!wr_iot_restart_restore_step(&s));assert(!wr_iot_restart_restore_step(&s));
 guest_ok=0;assert(!wr_iot_restart_restore_step(&s)&&phase==4);guest_ok=1;
 assert(!wr_iot_restart_restore_step(&s));assert(!wr_iot_restart_restore_step(&s)&&phase==5);
 services_ok=0;assert(!wr_iot_restart_restore_step(&s));services_ok=1;
 assert(wr_iot_restart_restore_step(&s)&&s.phase==WR_RESTORE_PREPARED&&ups==1);
 assert(s.main.generation==&s.generation&&s.guest.main==&s.main&&s.services.main==&s.main);
 int before=guest_calls;wr_iot_rc_shutdown.pending=SIGTERM;
 assert(!wr_iot_restart_restore_step(&s)&&guest_calls==before+1&&ups==1);
 wr_iot_rc_shutdown.pending=0;guest_ok=0;assert(!wr_iot_restart_restore_step(&s)&&ups==1);
 guest_ok=1;
 struct wr_iot_control_request request={.id="01000000000000000000000000000000",.created=10,.request={.enabled=1}};
 request.request.password[0]='x';assert(!wr_iot_restart_restore_handoff(&s,&request)&&!rebind_calls);request.request.password[0]=0;
 request.id[1]='2';assert(!wr_iot_restart_restore_handoff(&s,&request)&&!rebind_calls);request.id[1]='1';
 assert(!wr_iot_restart_restore_handoff(&s,&request)&&rebind_calls==1&&s.phase==WR_RESTORE_HANDOFF);
 assert(!wr_iot_restart_restore_handoff(&s,&request)&&rebind_calls==1);
 assert(!wr_iot_restart_restore_step(&s)&&rebind_calls==1);
 assert(!wr_iot_restart_restore_rebind_current(&s)&&active_reads==1);active_ok=1;
 assert(wr_iot_restart_restore_rebind_current(&s)&&active_reads==2);
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_restore_rebind_current(&s)&&active_reads==2);wr_iot_rc_shutdown.pending=0;
 s.main.generation=NULL;assert(!wr_iot_restart_restore_rebind_current(&s)&&active_reads==2);s.main.generation=&s.generation;
 assert(wr_iot_restart_restore_rebind_current(&s)&&rebind_calls==1);
 puts("PASS restore orchestration: stable embedded ownership, profile/Main/Guest/services order, uncertain Main not replayed, refusal retains phase, pending delegated to Guest, no baseline release; component actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restore-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
