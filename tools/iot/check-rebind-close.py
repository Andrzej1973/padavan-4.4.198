#!/usr/bin/env python3
"""Compose startup failure owner with actual CLOSE controller; transport injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
body=r'''
#include <unistd.h>
#include <fcntl.h>
#include "rebind-close.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int readable=1,guard=1,closed_ok=1;
static unsigned long long observed_serial=0x100000001ULL;
int wr_iot_service_guard_dup(void){return guard?open("/dev/null",O_RDONLY):-1;}
int wr_iot_rebind_open_recovery(const struct wr_iot_rebind_open_controller *o,struct wr_iot_driver_open_recovery_result *r){assert(o->attempt.request_id[0]==1);*r=(struct wr_iot_driver_open_recovery_result){2,2,3};return readable;}
int wr_iot_driver_attempt_closed(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_closed_result *r){assert(a->request_id[0]==1);*r=(struct wr_iot_driver_closed_result){2,2,3,observed_serial};return closed_ok;}
#include "rebind-close.c"
int main(void){
 struct wr_iot_start_close s={0};
 struct wr_iot_rebind_start rebind={.owner=getpid(),.identity={2,2},.open_id={1},.physical={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}}};
 struct wr_iot_start_admission owner={.admitted=1,.mutation_started=1,.staged=1,.reopened=2};
 owner.snapshot.active=owner.snapshot.token=1;owner.snapshot.owner=getpid();
 rebind.admission=owner;
 struct wr_iot_rebind_open_controller o={.attempt={{2,2},{1}},.owner=getpid(),.phase=WR_REBIND_OPEN_RETAINED};
 wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=SIGTERM;
 guard=0;assert(!wr_iot_rebind_close_step(&s,&rebind,&o)&&!s.owner);guard=1;
 o.attempt.identity.device_generation=4;assert(!wr_iot_rebind_close_step(&s,&rebind,&o)&&!s.owner);o.attempt.identity.device_generation=2;
 readable=0;assert(!wr_iot_rebind_close_step(&s,&rebind,&o)&&!closes);readable=1;
 close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 assert(!wr_iot_rebind_close_step(&s,&rebind,&o)&&closes==1&&s.close.phase==WR_IOT_CLOSE_UNCERTAIN);
 o.attempt.request_id[1]=1;assert(!wr_iot_rebind_close_step(&s,&rebind,&o)&&!progresses);o.attempt.request_id[1]=0;
 progress_result=WR_IOT_DRIVER_CLOSE_PENDING;
 assert(!wr_iot_rebind_close_step(&s,&rebind,&o)&&closes==1&&progresses==1);
 progress_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(!wr_iot_rebind_close_step(&s,&rebind,&o)&&s.close.phase==WR_IOT_CLOSE_REFERENCE_RETIRED);
 release_result=WR_IOT_DRIVER_CLOSE_PENDING;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));
 release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));
 closed_ok=0;assert(!wr_iot_rebind_close_step(&s,&rebind,&o)&&!s.close_serial);closed_ok=1;
 assert(wr_iot_rebind_close_step(&s,&rebind,&o)&&s.close_serial==observed_serial);
 observed_serial++;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));observed_serial--;
 assert(wr_iot_rebind_close_step(&s,&rebind,&o)&&closes==1);
 assert(owner.snapshot.active&&owner.snapshot.token==1&&wr_iot_rc_shutdown.pending==SIGTERM);

 o.busy=1;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));o.busy=0;
 rebind.physical.generation=9;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));rebind.physical.generation=2;
 rebind.open_id[1]=1;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));rebind.open_id[1]=0;
 rebind.physical.epoch=2;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));rebind.physical.epoch=1;
 rebind.admission.reopened=1;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));rebind.admission.reopened=2;
 rebind.owner++;assert(!wr_iot_rebind_close_step(&s,&rebind,&o));rebind.owner=getpid();
 assert(wr_iot_rebind_close_step(&s,&rebind,&o)&&closes==1);
 puts("PASS rebind exact new-epoch CLOSE handoff plus actual CLOSE controller: uncertain submission once, bounded progress/release, immutable identity, full64 serial/fresh CLOSED, foreign OPEN ID, old epoch and wrong owner refused; snapshot held; transport/resources injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-rebind-close-') as d:
 unit=Path(d)/'check.c';binary=Path(d)/'check';unit.write_text(prefix+body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
