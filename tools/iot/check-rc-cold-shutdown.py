"""Actual RC cold shutdown CLOSED predicate with existing CLOSE observer actor."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "rc-cold-shutdown.h"
#include "activation-observe.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static struct wr_iot_activation_owner backend;
static struct {pid_t owner;} rebind;
static const struct wr_iot_cold_owner *wr_iot_cold_backend_parent;
static struct wr_iot_driver_identity wr_iot_cold_backend_identity;
static int depth,observer_ok=1,drift;
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_activation_owner_closed(const struct wr_iot_activation_owner*s,const struct wr_iot_control_result*r,struct wr_iot_driver_closed_result*out){
 assert(depth&&s==&backend&&r->created==8&&!strcmp(r->id,backend.stop.id));
 *out=(struct wr_iot_driver_closed_result){5,2,7,9};if(drift==1)out->adapter_epoch++;if(drift==2)out->device_generation++;if(drift==3)out->open_token=0;if(drift==4)out->close_serial=0;if(drift==5)out->open_token++;if(drift==6)out->close_serial++;
 return observer_ok;
}
#include "rc-cold-shutdown.inc"
int main(void){
 struct wr_iot_cold_owner p={0};struct wr_iot_cold_handoff h={0};struct wr_iot_rc_quiesce off={0};struct wr_iot_driver_closed_result out;
 p.owner=getpid();p.main.identity=(struct wr_iot_driver_identity){5,2};wr_iot_cold_backend_parent=&p;wr_iot_cold_backend_identity=p.main.identity;
 h.owner=getpid();h.parent=&p;h.identity=p.main.identity;h.attempted=h.backend_claimed=1;h.phase=WR_COLD_HANDOFF_WAIT;h.created=7;memset(h.id,'1',32);
 backend.owner=backend.start.owner=backend.stop.owner=getpid();backend.phase=WR_IOT_OWNER_OFF;backend.start.phase=WR_IOT_RUN_STOPPED;
 backend.start.input.created=7;memcpy(backend.start.input.id,h.id,33);backend.start.open.attempt.identity=p.main.identity;
 backend.stop.stop.close.request.open_token=7;backend.stop.stop.close_serial=9;
 backend.stop.active=&backend.start;backend.stop.complete=1;backend.stop.created=8;memset(backend.stop.id,'2',32);
 off.owner=getpid();off.complete=1;off.created=8;memcpy(off.id,backend.stop.id,33);
 wr_iot_rc_shutdown.active=wr_iot_rc_shutdown.radio_off_owned=1;wr_iot_rc_shutdown.pending=SIGTERM;
 assert(wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out)&&out.close_serial==9&&!depth);
 for(drift=1;drift<=6;drift++)assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out)&&!out.adapter_epoch&&!depth);
 drift=0;
 observer_ok=0;assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out));observer_ok=1;
 off.desired.ssid[0]='x';assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out));off.desired.ssid[0]=0;
 off.resume_needed=1;assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out));off.resume_needed=0;
 off.created++;assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out));off.created--;
 wr_iot_rc_shutdown.pending=0;assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out));wr_iot_rc_shutdown.pending=SIGTERM;
 backend.phase=WR_IOT_OWNER_ACTIVE;assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out));backend.phase=WR_IOT_OWNER_OFF;
 rebind.owner=getpid();assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out));rebind.owner=0;
 h.identity.adapter_epoch++;assert(!wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out));h.identity.adapter_epoch--;
 assert(wr_iot_rc_cold_shutdown_closed(&p,&h,&off,&out)&&!depth);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-stop-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS exact cold post-handoff shutdown CLOSED: bound parent/ON/OFF identity, pending signal and complete no-resume OFF, stale/ACTIVE/rebind/credential refusal, zero output on failure; existing CLOSED observer actor')
