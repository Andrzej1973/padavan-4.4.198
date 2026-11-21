#!/usr/bin/env python3
"""Compose startup failure owner with actual CLOSE controller; transport injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
body=r'''
#include <unistd.h>
#include <fcntl.h>
#include "start-close.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int readable=1,guard=1,closed_ok=1;
static unsigned long long observed_serial=0x100000001ULL;
int wr_iot_service_guard_dup(void){return guard?open("/dev/null",O_RDONLY):-1;}
int wr_iot_open_controller_recovery_read(const struct wr_iot_open_controller *o,struct wr_iot_driver_open_recovery_result *r){assert(o->attempt.request_id[0]==1);*r=(struct wr_iot_driver_open_recovery_result){1,2,3};return readable;}
int wr_iot_driver_attempt_closed(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_closed_result *r){assert(a->request_id[0]==1);*r=(struct wr_iot_driver_closed_result){1,2,3,observed_serial};return closed_ok;}
#include "start-close.c"
#include "start-closed-rollback.h"
static int bridge=1,resource_fail,finished;
int wr_iot_bss_is_down(void){return 1;}
int wr_iot_bridge_set_up(int up){assert(!up);return !resource_fail;}
int wr_iot_bridge_detach(void){return 1;}
int wr_iot_bridge_remove(void){bridge=0;return 1;}
int wr_iot_dns_activation_recovery_state(void){return 0;}
int wr_iot_dns_activation_abort(void){assert(0);return 0;}
unsigned int if_nametoindex(const char *n){assert(!strcmp(n,"br-iot"));return bridge;}
int wr_iot_request_snapshot_restore(struct wr_iot_request_snapshot *s){assert(!bridge);s->recovering=s->restored=1;return 1;}
int wr_iot_request_snapshot_restored_current(struct wr_iot_request_snapshot *s){return s->recovering&&s->restored&&!bridge;}
int wr_iot_request_snapshot_finish(struct wr_iot_request_snapshot *s){assert(s->restored&&!bridge);s->active=0;finished++;return 1;}
#include "start-closed-rollback.c"

int main(void){
 struct wr_iot_start_close s={0};
 struct wr_iot_start_admission owner={.admitted=1,.mutation_started=1,.staged=1,.idle={1,2,1}};
 owner.snapshot.active=owner.snapshot.token=1;owner.snapshot.owner=getpid();
 struct wr_iot_open_controller o={.attempt={{1,2},{1}},.owner=getpid(),.phase=WR_IOT_OPEN_RECOVERY};
 wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=SIGTERM;
 guard=0;assert(!wr_iot_start_close_step(&s,&owner,&o)&&!s.owner);guard=1;
 o.attempt.identity.device_generation=4;assert(!wr_iot_start_close_step(&s,&owner,&o)&&!s.owner);o.attempt.identity.device_generation=2;
 readable=0;assert(!wr_iot_start_close_step(&s,&owner,&o)&&!closes);readable=1;
 close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 assert(!wr_iot_start_close_step(&s,&owner,&o)&&closes==1&&s.close.phase==WR_IOT_CLOSE_UNCERTAIN);
 o.attempt.request_id[1]=1;assert(!wr_iot_start_close_step(&s,&owner,&o)&&!progresses);o.attempt.request_id[1]=0;
 progress_result=WR_IOT_DRIVER_CLOSE_PENDING;
 assert(!wr_iot_start_close_step(&s,&owner,&o)&&closes==1&&progresses==1);
 progress_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(!wr_iot_start_close_step(&s,&owner,&o)&&s.close.phase==WR_IOT_CLOSE_REFERENCE_RETIRED);
 release_result=WR_IOT_DRIVER_CLOSE_PENDING;assert(!wr_iot_start_close_step(&s,&owner,&o));
 release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;assert(!wr_iot_start_close_step(&s,&owner,&o));
 closed_ok=0;assert(!wr_iot_start_close_step(&s,&owner,&o)&&!s.close_serial);closed_ok=1;
 assert(wr_iot_start_close_step(&s,&owner,&o)&&s.close_serial==observed_serial);
 observed_serial++;assert(!wr_iot_start_close_step(&s,&owner,&o));observed_serial--;
 assert(wr_iot_start_close_step(&s,&owner,&o)&&closes==1);
 assert(owner.snapshot.active&&owner.snapshot.token==1&&wr_iot_rc_shutdown.pending==SIGTERM);

 struct wr_iot_start_network network={.phase=WR_IOT_NET_READY,.attempted=127};
 struct wr_iot_start_network_rollback rollback={0};
 resource_fail=1;assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&o,&s)&&rollback.phase==WR_IOT_ROLL_BRIDGE_DOWN&&owner.snapshot.active);
 resource_fail=0;observed_serial++;
 assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&o,&s)&&rollback.phase==WR_IOT_ROLL_BRIDGE_DOWN);
 observed_serial--;
 for(unsigned n=0;n<6;n++)assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&o,&s));
 assert(rollback.phase==WR_IOT_ROLL_FINISH&&owner.snapshot.active&&owner.snapshot.recovering);
 observed_serial++;assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&o,&s)&&!finished);
 observed_serial--;assert(wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&o,&s)&&finished==1&&!owner.snapshot.active);
 assert(wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&o,&s)&&finished==1);
 puts("PASS startup CLOSE handoff plus actual CLOSE controller: uncertain submission once, bounded progress/release, immutable identity, full64 serial/fresh CLOSED, post-CLOSE bridge/DNS/settings rollback with fresh serial before final release; transport/resources injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-start-close-') as d:
 unit=Path(d)/'check.c';binary=Path(d)/'check';unit.write_text(prefix+body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
