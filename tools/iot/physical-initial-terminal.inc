#ifndef WR_IOT_PHYSICAL_INITIAL_TERMINAL_IMPL
#define WR_IOT_PHYSICAL_INITIAL_TERMINAL_IMPL
/* PID identity cache only. Caller owns RTNL/adapter lifetime, serializes all
 * access, and drops detached caches outside locks. Not native adapter pins. */
#include "physical-initial-types.h"
#include "physical-stop-lifetime.h"
#include "physical-stop-pin-types.h"
#include "physical-initial-terminal-types.h"
static inline int wr_iot_physical_initial_terminal_prepare(
 struct wr_iot_physical_initial_terminal *s,const struct wr_iot_physical_initial_request *q)
{
 if(!s||s->owner||s->ready||s->status||s->cleanup_phase||!wr_iot_physical_initial_valid(q,0)||
    (q->action!=WR_STOP_CANCEL&&q->action!=WR_STOP_RELEASE))return 0;
 s->owner=get_pid(task_pid(current));if(!s->owner)return 0;
 s->request=*q;s->status=q->action==WR_STOP_CANCEL?WR_STOP_CANCELLED:WR_STOP_RELEASED;
 return 1;
}
/* Prepared but not yet committed cleanup may resume only for this exact
 * issuer and terminal action. Never replace a pending cache on retry. */
static inline int wr_iot_physical_initial_terminal_matches(
 const struct wr_iot_physical_initial_terminal *s,
 const struct wr_iot_physical_initial_request *q)
{
 struct wr_iot_physical_initial_response match;
 if(!s||!s->owner||s->owner!=task_pid(current))return 0;
 match.identity=s->request;match.status=s->status;
 return wr_iot_physical_initial_reply_matches(&match,q);
}
/* Read real post-cleanup metadata, not user-supplied completion booleans.
 * Binding must keep lifetime active until synchronous native pins_drop returns. */
static inline int wr_iot_physical_initial_terminal_commit(
 struct wr_iot_physical_initial_terminal *s,
 const struct wr_iot_physical_initial_record *record,
 const struct wr_iot_physical_stop_lifetime *life,
 const struct wr_iot_physical_stop_pins *slot,const struct wr_iot_physical_stop_pins *local)
{
 struct wr_iot_physical_initial_response match;
 if(!s||!s->owner||s->owner!=task_pid(current)||s->ready||!record||record->task||
    !record->origin.main_device||!record->origin.iot_device||
    !record->origin.lifetime_serial||!record->origin.epoch||
    !record->origin.generation||!record->origin.idle_serial||
    !life||life->active||life->serial!=record->origin.lifetime_serial||
    life->main_device||life->main_ticket_valid||life->main_generation||
    life->main_open_token||life->arm_radio_serial||life->arm_radio_epoch||
    life->arm_record_serial||life->arm_request.action||!slot||!local||slot==local||
    slot->module||slot->task||slot->device||local->module||local->task||local->device||
    record->serial!=s->request.attempt)return 0;
 if(s->request.action==WR_STOP_CANCEL){
  if(record->status!=WR_STOP_ARMED||record->completion_epoch)return 0;
 }else if(s->request.action==WR_STOP_RELEASE){
  if(record->status!=WR_STOP_COMPLETE||record->completion_epoch<=record->origin.epoch)return 0;
 }else return 0;
 match.identity=record->request;match.identity.action=s->request.action;
 match.identity.attempt=record->serial;match.status=s->status;
 if(!wr_iot_physical_initial_reply_matches(&match,&s->request))return 0;
 s->ready=1;return 1;
}
static inline int wr_iot_physical_initial_terminal_reply(
 const struct wr_iot_physical_initial_terminal *s,
 const struct wr_iot_physical_initial_request *q,unsigned char *wire,unsigned length)
{
 struct wr_iot_physical_initial_response match;unsigned i;
 if(!wire||length!=64)return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!s||!s->ready||s->owner!=task_pid(current))return 0;
 match.identity=s->request;match.status=s->status;
 if(!wr_iot_physical_initial_reply_matches(&match,q))return 0;
 return wr_iot_physical_initial_encode(wire,length,&s->request,s->status);
}
static inline int wr_iot_physical_initial_terminal_clear(struct wr_iot_physical_initial_terminal *s)
{
 struct pid *owner;struct wr_iot_physical_initial_terminal empty={0};
 if(!s||!s->owner)return 0;
 owner=s->owner;*s=empty;put_pid(owner);return 1;
}
#endif
