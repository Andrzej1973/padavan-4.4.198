#ifndef WR_IOT_PHYSICAL_STOP_TERMINAL_IMPL
#define WR_IOT_PHYSICAL_STOP_TERMINAL_IMPL
/* Kernel-only bounded terminal cache. Caller serializes access, pins adapter
 * for each call and keeps cache outside resources freed by radio close.
 * get_pid/put_pid retain only PID identity, not adapter/module/RF ownership.
 * Clear only detached cache outside locks at final adapter retirement or
 * before a newly admitted ARM replaces the previous terminal transaction. */
#include "physical-stop-response.h"
#include "physical-stop-terminal-types.h"
static inline int wr_iot_physical_stop_terminal_prepare(struct wr_iot_physical_stop_terminal *s,
 const struct wr_iot_physical_stop_request *r)
{
 if(!s||s->owner||s->status||s->ready||!wr_iot_physical_stop_request_valid(r)||
    (r->action!=WR_STOP_CANCEL&&r->action!=WR_STOP_RELEASE))return 0;
 s->owner=get_pid(task_pid(current));if(!s->owner)return 0;
 {struct wr_iot_physical_stop_origin empty={0};s->origin=empty;}
 s->request=*r;s->status=r->action==WR_STOP_CANCEL?WR_STOP_CANCELLED:WR_STOP_RELEASED;
 return 1;
}
/* Receipts must be derived from actual record/pin/fence cleanup in binding,
 * never copied from user input. Until then a prepared cache cannot reply. */
static inline int wr_iot_physical_stop_terminal_commit(struct wr_iot_physical_stop_terminal *s,
 int record_idle,int refs_returned,int lifetime_ended)
{
 if(!s||!s->owner||s->owner!=task_pid(current)||s->ready||
    record_idle!=1||refs_returned!=1||lifetime_ended!=1)return 0;
 s->ready=1;return 1;
}
static inline int wr_iot_physical_stop_terminal_reply(const struct wr_iot_physical_stop_terminal *s,
 const struct wr_iot_physical_stop_request *r,unsigned char *wire,unsigned int length)
{
 unsigned i;
 if(!wire||length!=64)return 0;
 for(i=0;i<length;i++)wire[i]=0;
 if(!s||!s->ready||!s->owner||s->owner!=task_pid(current)||
    !wr_iot_physical_stop_request_valid(r)||r->action!=s->request.action||
    r->attempt!=s->request.attempt||r->epoch!=s->request.epoch||
    r->generation!=s->request.generation||r->open_token!=s->request.open_token||
    r->closed_serial!=s->request.closed_serial)return 0;
 for(i=0;i<16;i++)if(r->nonce[i]!=s->request.nonce[i])return 0;
 return wr_iot_physical_stop_response_encode(wire,length,r,r->attempt,s->status);
}
static inline int wr_iot_physical_stop_terminal_clear(struct wr_iot_physical_stop_terminal *s)
{
 struct pid *owner;struct wr_iot_physical_stop_terminal empty={0};
 if(!s||!s->owner)return 0;
 owner=s->owner;*s=empty;put_pid(owner);return 1;
}

#endif
