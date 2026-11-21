#include <string.h>
#include <unistd.h>
#include "reopen-start.h"
#include "request-stage.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
int wr_iot_reopen_start_begin(struct wr_iot_start_admission *s,
 const struct wr_iot_reopen_witness *w)
{
 struct wr_iot_reopen_witness saved;int guard,ok=0;
 if(!s||!w||s->admitted||s->staged||s->mutation_started||
    s->reopened||s->snapshot.active||s->snapshot.token||!wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending)return 0;
 saved=*w;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_reopen_witness_current(w)||memcmp(w,&saved,sizeof(saved))||
    !wr_iot_request_snapshot_take(&s->snapshot))goto done;
 if(wr_iot_rc_shutdown.pending||memcmp(w,&saved,sizeof(saved))||
    !wr_iot_reopen_witness_current(w)){
  /* Read-only snapshot only. Failed finish retains its existing owner/guard. */
  (void)wr_iot_request_snapshot_finish(&s->snapshot);goto done;
 }
 /* Epoch/generation are shared startup identity; serial is the retained
  * CLOSED serial, not a fabricated initial-idle observation serial. Later
  * stages must explicitly use this witness, never the initial-idle reader. */
 s->idle.epoch=w->attempt.identity.adapter_epoch;
 s->idle.generation=w->attempt.identity.device_generation;
 s->idle.serial=w->close_serial;
 s->admitted=1;s->reopened=1;ok=1;
 done:wr_iot_service_guard_leave(guard);return ok;
}
int wr_iot_reopen_start_stage(struct wr_iot_start_admission *s,
 const struct wr_iot_reopen_witness *w,const char *(*read)(void *,const char *),
 void *context,int router,int radio,int mode)
{
 struct wr_iot_reopen_witness saved;int fd;
 if(!s||!w||!read||!s->reopened||!s->admitted||s->mutation_started||s->staged||
    !s->snapshot.active||s->snapshot.owner!=getpid()||s->snapshot.token!=1||
    s->snapshot.recovering||s->snapshot.disabling||!wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||s->idle.epoch!=w->attempt.identity.adapter_epoch||
    s->idle.generation!=w->attempt.identity.device_generation||s->idle.serial!=w->close_serial)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(!wr_iot_reopen_witness_current(w)||wr_iot_rc_shutdown.pending)return 0;
 saved=*w;
 s->mutation_started=1;
 if(!wr_iot_request_stage_from(read,context,router,radio,mode)||
    wr_iot_rc_shutdown.pending||memcmp(w,&saved,sizeof(saved))||
    !wr_iot_reopen_witness_current(w))return 0;
 s->staged=1;return 1;
}
