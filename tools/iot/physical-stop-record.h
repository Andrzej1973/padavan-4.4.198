/* Unbound Linux-side attempt metadata. Not an RF/DMA certificate by itself.
 * All access uses the existing adapter MacTabLock. Caller separately pins the
 * adapter, module and task from arm through successful release. No allocations,
 * waits, firmware fields or global queue changes occur here. */
#ifndef WR_IOT_PHYSICAL_STOP_RECORD_H
#define WR_IOT_PHYSICAL_STOP_RECORD_H
#include "peer-close-executor.h"
#include "peer-table-owner.h"
enum wr_iot_physical_stop_phase {WR_PHYS_STOP_IDLE,WR_PHYS_STOP_ARMED,
 WR_PHYS_STOP_RUNNING,WR_PHYS_STOP_COMPLETE,WR_PHYS_STOP_FAILED};
struct wr_iot_physical_stop_record {
 unsigned long long serial,epoch,generation,open_token,closed_serial;
 unsigned long long completion_epoch;
 unsigned char nonce[16];
 const void *task;
 enum wr_iot_physical_stop_phase phase;
};
static inline int wr_iot_physical_stop_nonce_equal(const unsigned char *a,const unsigned char *b)
{unsigned i;if(!a||!b)return 0;for(i=0;i<16;i++)if(a[i]!=b[i])return 0;return 1;}
static inline int wr_iot_physical_stop_arm(struct wr_iot_physical_stop_record *s,
 unsigned long long epoch,unsigned long long generation,
 unsigned long long token,unsigned long long closed_serial,
 const unsigned char *nonce,const void *task,const struct wr_iot_peer_close_executor *executor)
{
 unsigned i,nonzero=0;
 if(!s||s->phase!=WR_PHYS_STOP_IDLE||s->task||!epoch||!generation||
    !token||!closed_serial||!nonce||!task||s->serial==~0ULL||
    !wr_iot_peer_close_executor_idle(executor)||
    (s->serial&&wr_iot_physical_stop_nonce_equal(s->nonce,nonce)))return 0;
 for(i=0;i<16;i++)nonzero|=nonce[i];
 if(!nonzero)return 0;
 ++s->serial;s->completion_epoch=0;s->epoch=epoch;s->generation=generation;s->open_token=token;
 s->closed_serial=closed_serial;s->task=task;
 for(i=0;i<16;i++)s->nonce[i]=nonce[i];
 s->phase=WR_PHYS_STOP_ARMED;return 1;
}
static inline int wr_iot_physical_stop_matches(const struct wr_iot_physical_stop_record *s,
 unsigned long long serial,unsigned long long epoch,unsigned long long generation,
 const unsigned char *nonce,const void *task)
{return s&&s->phase!=WR_PHYS_STOP_IDLE&&serial&&s->serial==serial&&
 s->epoch==epoch&&s->generation==generation&&task&&s->task==task&&
 wr_iot_physical_stop_nonce_equal(s->nonce,nonce);}
/* Only a never-entered arm may be cancelled. Caller still holds its pinned
 * task/module/adapter references until this succeeds, then releases them once.
 * Cancellation keeps nonce/serial replay history; RUNNING/FAILED never cancel. */
static inline int wr_iot_physical_stop_cancel(struct wr_iot_physical_stop_record *s,
 unsigned long long serial,unsigned long long epoch,unsigned long long generation,
 const unsigned char *nonce,const void *task)
{
 if(!wr_iot_physical_stop_matches(s,serial,epoch,generation,nonce,task)||
    s->phase!=WR_PHYS_STOP_ARMED)return 0;
 s->epoch=s->generation=s->open_token=s->closed_serial=s->completion_epoch=0;s->task=0;
 s->phase=WR_PHYS_STOP_IDLE;return 1;
}
static inline int wr_iot_physical_stop_begin(struct wr_iot_physical_stop_record *s,
 unsigned long long serial,unsigned long long epoch,unsigned long long generation,
 const unsigned char *nonce,const void *task)
{
 if(!wr_iot_physical_stop_matches(s,serial,epoch,generation,nonce,task)||
    s->phase!=WR_PHYS_STOP_ARMED)return 0;
 s->phase=WR_PHYS_STOP_RUNNING;return 1;
}
/* Bind ONLY after the real legacy body AND executor leave, not ndo_stop/ioctl
 * status. A failed/unfinished close retains task/module ownership for recovery.
 * These software postconditions do not independently prove RF retirement. */
static inline int wr_iot_physical_stop_finish_at_epoch(struct wr_iot_physical_stop_record *s,
 unsigned long long serial,unsigned long long epoch,unsigned long long generation,
 const unsigned char *nonce,const void *task,int body_succeeded,
 const struct wr_iot_peer_close_executor *executor,
 const struct wr_iot_peer_table_owner *table,unsigned int legacy_close_state,
 unsigned long long observed_completion_epoch)
{
 if(!wr_iot_physical_stop_matches(s,serial,epoch,generation,nonce,task)||
    s->phase!=WR_PHYS_STOP_RUNNING)return 0;
 if(!body_succeeded||!observed_completion_epoch||observed_completion_epoch<epoch||
    !wr_iot_peer_close_executor_idle(executor)||!table||
    !table->closed||table->active||table->retained||table->poisoned||
    table->transactions||legacy_close_state!=2U){s->phase=WR_PHYS_STOP_FAILED;return 0;}
 s->completion_epoch=observed_completion_epoch;s->phase=WR_PHYS_STOP_COMPLETE;return 1;
}
/* Compatibility for model fixtures whose radio epoch does not change.
 * Actual physical-close binding must sample the real resulting epoch and use
 * finish_at_epoch, not assume that the pre-close epoch survived teardown. */
static inline int wr_iot_physical_stop_finish(struct wr_iot_physical_stop_record *s,
 unsigned long long serial,unsigned long long epoch,unsigned long long generation,
 const unsigned char *nonce,const void *task,int body_succeeded,
 const struct wr_iot_peer_close_executor *executor,
 const struct wr_iot_peer_table_owner *table,unsigned int legacy_close_state)
{return wr_iot_physical_stop_finish_at_epoch(s,serial,epoch,generation,nonce,task,
 body_succeeded,executor,table,legacy_close_state,epoch);}
/* Read-only exact-attempt observation for a future authenticated transport.
 * Adapter/task pins and lock remain required; not a future lease. */
static inline int wr_iot_physical_stop_observe(const struct wr_iot_physical_stop_record *s,
 unsigned long long serial,unsigned long long epoch,unsigned long long generation,
 unsigned long long token,unsigned long long closed_serial,
 const unsigned char *nonce,const void *task)
{
 return wr_iot_physical_stop_matches(s,serial,epoch,generation,nonce,task)&&
  token&&closed_serial&&s->open_token==token&&s->closed_serial==closed_serial&&
  s->phase==WR_PHYS_STOP_COMPLETE;
}
static inline int wr_iot_physical_stop_release(struct wr_iot_physical_stop_record *s,
 unsigned long long serial,unsigned long long epoch,unsigned long long generation,
 const unsigned char *nonce,const void *task)
{
 if(!wr_iot_physical_stop_matches(s,serial,epoch,generation,nonce,task)||
    s->phase!=WR_PHYS_STOP_COMPLETE)return 0;
 /* Preserve monotonically increasing serial across reopen; never reuse it. */
 s->epoch=s->generation=s->open_token=s->closed_serial=s->completion_epoch=0;s->task=0;
 /* Retain the last nonsecret nonce to refuse immediate replay. Historical
  * nonce uniqueness still belongs to the serialized RC issuer. */
 s->phase=WR_PHYS_STOP_IDLE;return 1;
}
#endif
