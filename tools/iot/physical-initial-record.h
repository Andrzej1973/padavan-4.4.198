/* Initial-origin physical attempt state; not installed in the adapter yet.
 * Access under existing adapter lifetime/locks. Native references/pins must
 * remain owned by the binding; this metadata never acquires or frees them. */
#ifndef WR_IOT_PHYSICAL_INITIAL_RECORD_H
#define WR_IOT_PHYSICAL_INITIAL_RECORD_H
#include "physical-initial-origin.h"
#include "physical-initial-wire.h"
static inline int wr_iot_physical_initial_record_matches(
 const struct wr_iot_physical_initial_record *s,
 const struct wr_iot_physical_initial_request *q,const void *task)
{
 unsigned i;
 if(!s||!task||s->task!=task||!s->serial||!wr_iot_physical_initial_valid(q,0)||
    q->epoch!=s->request.epoch||q->generation!=s->request.generation||
    q->idle_serial!=s->request.idle_serial||
    (q->action!=WR_STOP_ARM&&q->attempt!=s->serial))return 0;
 for(i=0;i<16;i++)if(q->nonce[i]!=s->request.nonce[i])return 0;
 return 1;
}
static inline int wr_iot_physical_initial_record_arm(
 struct wr_iot_physical_initial_record *s,
 const struct wr_iot_physical_initial_request *q,const void *task,
 const struct wr_iot_physical_initial_origin *origin,
 const struct wr_iot_physical_stop_lifetime *life,
 const struct wr_iot_interface_ref *iot)
{
 if(!s||s->task||s->status||s->serial==~0ULL||!task||
    !wr_iot_physical_initial_valid(q,0)||q->action!=WR_STOP_ARM||
    !wr_iot_physical_initial_main_binding(origin,life)||
    !wr_iot_physical_initial_history(origin,iot)||q->epoch!=origin->epoch||
    q->generation!=origin->generation||q->idle_serial!=origin->idle_serial)return 0;
 s->serial++;s->task=task;s->request=*q;s->request.attempt=s->serial;
 s->origin=*origin;s->status=WR_STOP_ARMED;return 1;
}
static inline int wr_iot_physical_initial_record_running(
 struct wr_iot_physical_initial_record *s,
 const struct wr_iot_physical_initial_request *q,const void *task,
 const struct wr_iot_physical_stop_lifetime *life)
{
 if(!wr_iot_physical_initial_record_matches(s,q,task)||
    s->status!=WR_STOP_ARMED||!wr_iot_physical_initial_main_binding(&s->origin,life)||
    !life->main_ticket_valid||life->main_ticket.operation!=WR_RADIO_CLOSE||
    life->main_ticket.reset_kind||life->main_ticket.serial<=s->origin.idle_serial)return 0;
 s->status=WR_STOP_RUNNING;return 1;
}
/* Pure response from existing state; QUERY never submits work or marks COMPLETE.
 * COMPLETE publication and reference-return terminal paths remain unbound. */
static inline int wr_iot_physical_initial_record_reply(
 const struct wr_iot_physical_initial_record *s,
 const struct wr_iot_physical_initial_request *q,const void *task,
 unsigned char *wire,unsigned length)
{
 struct wr_iot_physical_initial_request reply;unsigned i,status;
 if(!wire||length!=64)return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!wr_iot_physical_initial_record_matches(s,q,task))return 0;
 status=s->status;
 if(q->action==WR_STOP_ARM&&status!=WR_STOP_ARMED)return 0;
 if(q->action!=WR_STOP_ARM&&q->action!=WR_STOP_QUERY)return 0;
 reply=*q;reply.attempt=s->serial;
 return wr_iot_physical_initial_encode(wire,length,&reply,status);
}
#endif
