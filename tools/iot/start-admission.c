#include <string.h>
#include <unistd.h>
#include "request-stage.h"
#include "start-admission.h"
#include "driver-api-client.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
int wr_iot_start_admission_begin(struct wr_iot_start_admission *s,const unsigned char *nonce)
{
 struct wr_iot_idle_result before,after;int guard;
 if(!s||s->reopened||s->mutation_started||s->staged||s->admitted||s->snapshot.active||s->snapshot.token||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_driver_initial_idle_read(nonce,&before)||
    wr_iot_rc_shutdown.pending||!wr_iot_request_snapshot_take(&s->snapshot)){
  wr_iot_service_guard_leave(guard);return 0;
 }
 /* Snapshot retains its own nested guard after the outer temporary hold.
  * No setter has run, so failure can discard only this read-only capture. */
 if(wr_iot_rc_shutdown.pending||!wr_iot_driver_initial_idle_read(nonce,&after)||
    before.epoch!=after.epoch||before.generation!=after.generation||
    !before.serial||after.serial<=before.serial||wr_iot_rc_shutdown.pending){
  (void)wr_iot_request_snapshot_finish(&s->snapshot);
  wr_iot_service_guard_leave(guard);return 0;
 }
 s->idle=after;s->admitted=1;wr_iot_service_guard_leave(guard);return 1;
}
int wr_iot_start_admission_cancel(struct wr_iot_start_admission *s)
{
 if(!s||s->mutation_started||s->staged||!s->snapshot.active||s->snapshot.recovering||s->snapshot.disabling)return 0;
 if(!wr_iot_request_snapshot_finish(&s->snapshot))return 0;
 memset(s,0,sizeof(*s));return 1;
}

int wr_iot_start_admission_stage(struct wr_iot_start_admission *s,const unsigned char *nonce,
 const char *(*read)(void *,const char *),void *context,int router_mode,int radio_on,int radio_mode)
{
 struct wr_iot_idle_result current;int fd;
 if(!s||s->reopened||!s->admitted||s->mutation_started||s->staged||!read||
    !s->snapshot.active||s->snapshot.owner!=getpid()||s->snapshot.token!=1||
    s->snapshot.recovering||s->snapshot.disabling||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd)||!wr_iot_driver_initial_idle_read(nonce,&current)||
    current.epoch!=s->idle.epoch||current.generation!=s->idle.generation||
    current.serial<=s->idle.serial||wr_iot_rc_shutdown.pending)return 0;
 s->idle=current;s->mutation_started=1;
 if(!wr_iot_request_stage_from(read,context,router_mode,radio_on,radio_mode))return 0;
 if(wr_iot_rc_shutdown.pending)return 0;
 s->staged=1;return 1;
}
