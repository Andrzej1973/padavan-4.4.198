#include <string.h>
#include <unistd.h>
#include "rebind-start.h"
#include "request-stage.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
int wr_iot_rebind_start_begin(struct wr_iot_rebind_start *s,
 const struct wr_iot_physical_stop_request *physical,const unsigned char *open_id)
{
 struct wr_iot_driver_identity before={0},after={0};int guard,ok=0;unsigned i;
 if(!s||!physical||!open_id||s->owner||s->admission.admitted||
    s->admission.mutation_started||s->admission.snapshot.active||s->admission.snapshot.token||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_rebind_configuration_current(physical,open_id,&before)||
    !wr_iot_request_snapshot_take(&s->admission.snapshot))goto done;
 if(wr_iot_rc_shutdown.pending||!wr_iot_rebind_configuration_current(physical,open_id,&after)||
    before.adapter_epoch!=after.adapter_epoch||before.device_generation!=after.device_generation||
    wr_iot_rc_shutdown.pending){
  (void)wr_iot_request_snapshot_finish(&s->admission.snapshot);goto done;
 }
 s->owner=getpid();s->physical=*physical;s->identity=after;
 for(i=0;i<16;i++)s->open_id[i]=open_id[i];
 s->admission.admitted=1;s->admission.reopened=2;ok=1;
 done:wr_iot_service_guard_leave(guard);return ok;
}
int wr_iot_rebind_start_stage(struct wr_iot_rebind_start *s,
 const char *(*read)(void *,const char *),void *context,int router,int radio,int mode)
{
 struct wr_iot_driver_identity current={0};int fd;
 if(!s||!read||s->owner!=getpid()||s->admission.reopened!=2||
    !s->admission.admitted||s->admission.mutation_started||s->admission.staged||
    !s->admission.snapshot.active||s->admission.snapshot.owner!=getpid()||
    s->admission.snapshot.token!=1||s->admission.snapshot.recovering||
    s->admission.snapshot.disabling||!wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(!wr_iot_rebind_configuration_current(&s->physical,s->open_id,&current)||
    current.adapter_epoch!=s->identity.adapter_epoch||
    current.device_generation!=s->identity.device_generation||wr_iot_rc_shutdown.pending)return 0;
 s->admission.mutation_started=1;
 if(!wr_iot_request_stage_from(read,context,router,radio,mode)||wr_iot_rc_shutdown.pending||
    !wr_iot_rebind_configuration_current(&s->physical,s->open_id,&current)||
    current.adapter_epoch!=s->identity.adapter_epoch||
    current.device_generation!=s->identity.device_generation||wr_iot_rc_shutdown.pending)return 0;
 s->admission.staged=1;return 1;
}
