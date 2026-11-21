/* Prepared AP-stop record. All access under the adapter lifetime lock.
 * Operation serial comes from a verified caller owner; never infer it from BSS.
 * Device/BSS generation and adapter allocation lifetime are external pins. */
#ifndef WR_FT_AP_STOP_OWNER_H
#define WR_FT_AP_STOP_OWNER_H
#include "peer-table-owner.h"
enum wr_ft_ap_reset_phase {
 WR_FT_AP_RESET_NONE,WR_FT_AP_RESET_PREPARED,WR_FT_AP_RESET_IRQ_OFF,
 WR_FT_AP_RESET_WDS,WR_FT_AP_RESET_APCLI,WR_FT_AP_RESET_TABLE,
 WR_FT_AP_RESET_FINAL,WR_FT_AP_RESET_COMPLETE
};
enum wr_ft_ap_stop_retry {
 WR_FT_AP_STOP_RETRY_NONE,WR_FT_AP_STOP_RETRY_PHASE,
 WR_FT_AP_STOP_RETRY_WDS_NOT_WRITTEN,WR_FT_AP_STOP_RETRY_WDS_UNCERTAIN,
 WR_FT_AP_STOP_RETRY_TABLE_RETAINED
};
enum wr_ft_ap_wds_result {
 WR_FT_AP_WDS_PENDING,WR_FT_AP_WDS_NOT_WRITTEN,
 WR_FT_AP_WDS_APPLIED,WR_FT_AP_WDS_PARTIAL,WR_FT_AP_WDS_UNKNOWN
};
struct wr_ft_ap_wds_identity {
 const void *device;
 unsigned long generation,serial;
 unsigned int index,wcid;
 unsigned char address[6];
};
struct wr_ft_ap_stop_identity {
 const void *device;
 unsigned long operation,generation;
 unsigned int bss,whole_adapter;
};
struct wr_ft_ap_stop_owner {
 struct wr_ft_ap_stop_identity identity;
 unsigned long cache_ticket;
 unsigned int active,running,stage;
 unsigned long table_serial;
 enum wr_ft_ap_reset_phase reset_phase,resume_phase;
 unsigned int reset_cursor,reset_limit,wds_limit;
 unsigned int retry_kind,wds_valid,wds_retry;
 enum wr_ft_ap_wds_result wds_result;
 struct wr_ft_ap_wds_identity wds;
};
static inline int wr_ft_ap_wds_matches(const struct wr_ft_ap_wds_identity *a,
 const struct wr_ft_ap_wds_identity *b)
{
 unsigned int i;
 if(!a||!b||!a->device||!a->generation||!a->serial||!a->wcid||
    a->device!=b->device||a->generation!=b->generation||a->serial!=b->serial||
    a->index!=b->index||a->wcid!=b->wcid)return 0;
 for(i=0;i<6;i++)if(a->address[i]!=b->address[i])return 0;
 return 1;
}
static inline int wr_ft_ap_stop_matches(const struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id)
{
 return s&&id&&s->active&&id->device&&id->operation&&id->generation&&
  s->identity.device==id->device&&s->identity.operation==id->operation&&
  s->identity.generation==id->generation&&s->identity.bss==id->bss&&
  s->identity.whole_adapter==id->whole_adapter;
}
static inline int wr_ft_ap_stop_enter(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id)
{
 if(!s||!id||!id->device||!id->operation||!id->generation||
    id->whole_adapter>1||s->running)return 0;
 if(s->active&&(!wr_ft_ap_stop_matches(s,id)||
    s->retry_kind!=WR_FT_AP_STOP_RETRY_PHASE))return 0;
 if(!s->active){s->identity=*id;s->cache_ticket=0;s->stage=0;s->active=1;}
 s->retry_kind=WR_FT_AP_STOP_RETRY_NONE;s->running=1;return 1;
}
/* Bind only an actual reserved cache serial, before AP side effects. Caller
 * validates the cache reservation in the same critical section. */
static inline int wr_ft_ap_stop_bind(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long ticket)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!ticket||s->stage)return 0;
 if(s->cache_ticket&&s->cache_ticket!=ticket)return 0;
 s->cache_ticket=ticket;return 1;
}
/* Native phase success is a binding receipt. Failure retains prior stage. */
static inline int wr_ft_ap_stop_advance(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned int expected)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!s->cache_ticket||
    s->stage!=expected||expected>=3)return 0;
 s->stage++;return 1;
}
static inline int wr_ft_ap_stop_yield(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||s->wds_valid)return 0;
 s->running=0;s->retry_kind=WR_FT_AP_STOP_RETRY_PHASE;return 1;
}
static inline int wr_ft_ap_stop_finish(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||s->stage!=3||
    s->wds_valid||s->retry_kind!=WR_FT_AP_STOP_RETRY_NONE||
    (s->table_serial&&s->reset_phase!=WR_FT_AP_RESET_COMPLETE))return 0;
 *s=(struct wr_ft_ap_stop_owner){0};return 1;
}

/* The table serial is reserved by the peer-table owner before AP side effects.
 * Caller validates active/retained owner state under this same lock; bind or
 * retry only the same serial. This record does not itself reopen the table. */
static inline int wr_ft_ap_stop_reset_bind(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 unsigned int table_limit,unsigned int wds_limit)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!s->cache_ticket||!serial||
    table_limit<2||!wds_limit)return 0;
 if(s->table_serial)return s->table_serial==serial&&
  s->reset_limit==table_limit&&s->wds_limit==wds_limit;
 s->table_serial=serial;s->reset_phase=WR_FT_AP_RESET_PREPARED;
 s->resume_phase=WR_FT_AP_RESET_NONE;s->reset_cursor=0;
 s->reset_limit=table_limit;s->wds_limit=wds_limit;return 1;
}
static inline int wr_ft_ap_stop_reset_advance(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 enum wr_ft_ap_reset_phase expected)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!serial||
    s->table_serial!=serial||expected<WR_FT_AP_RESET_PREPARED||
    s->reset_phase!=expected||
    expected>=WR_FT_AP_RESET_COMPLETE)return 0;
 s->reset_phase=(enum wr_ft_ap_reset_phase)(expected+1);
 s->reset_cursor=0;return 1;
}
static inline int wr_ft_ap_stop_reset_cursor(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 enum wr_ft_ap_reset_phase phase,unsigned int cursor)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!serial||
    s->table_serial!=serial||s->reset_phase!=phase||
    phase<WR_FT_AP_RESET_WDS||phase>WR_FT_AP_RESET_TABLE||
    cursor<s->reset_cursor||
    cursor>(phase==WR_FT_AP_RESET_WDS?s->wds_limit:s->reset_limit))return 0;
 s->reset_cursor=cursor;return 1;
}
/* A failed table reset remains closed to ordinary writers. Park the AP
 * operation only after the same serial has been retained by the table owner. */
static inline int wr_ft_ap_stop_table_hold(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,
 const struct wr_iot_peer_table_owner *table,unsigned long serial)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!table||!serial||
    s->table_serial!=serial||s->reset_phase!=WR_FT_AP_RESET_TABLE||
    s->wds_valid||s->retry_kind!=WR_FT_AP_STOP_RETRY_NONE||
    !table->active||!table->retained||table->serial!=serial)return 0;
 s->running=0;s->retry_kind=WR_FT_AP_STOP_RETRY_TABLE_RETAINED;return 1;
}
/* Authenticate operation identity and serial before reopening only its
 * retained reservation. Caller holds the adapter lifetime/MacTab lock across
 * this composition; generic enter cannot consume TABLE_RETAINED state. */
static inline int wr_ft_ap_stop_table_resume(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,
 struct wr_iot_peer_table_owner *table,unsigned long serial)
{
 if(!wr_ft_ap_stop_matches(s,id)||s->running||!table||!serial||
    s->retry_kind!=WR_FT_AP_STOP_RETRY_TABLE_RETAINED||
    s->table_serial!=serial||s->reset_phase!=WR_FT_AP_RESET_TABLE||
    s->wds_valid||!table->active||!table->retained||
    table->serial!=serial||table->transactions)return 0;
 if(!wr_iot_peer_table_resume_retained(table,serial))return 0;
 s->running=1;s->retry_kind=WR_FT_AP_STOP_RETRY_NONE;return 1;
}
static inline int wr_ft_ap_stop_wds_begin(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 const struct wr_ft_ap_wds_identity *wds)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!serial||
    s->table_serial!=serial||
    (s->reset_phase!=WR_FT_AP_RESET_WDS&&s->reset_phase!=WR_FT_AP_RESET_TABLE)||
    s->wds_valid||!wds||!wds->device||!wds->generation||!wds->serial||
    !wds->wcid||wds->wcid>=s->reset_limit||wds->index>=s->wds_limit)
  return 0;
 s->wds=*wds;s->wds_valid=1;s->wds_retry=0;
 s->wds_result=WR_FT_AP_WDS_PENDING;return 1;
}
static inline int wr_ft_ap_stop_wds_not_written(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 const struct wr_ft_ap_wds_identity *wds)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!serial||
    s->table_serial!=serial||!s->wds_valid||
    !wr_ft_ap_wds_matches(&s->wds,wds)||
    (s->wds_result!=WR_FT_AP_WDS_PENDING&&s->wds_result!=WR_FT_AP_WDS_NOT_WRITTEN))
  return 0;
 s->wds_result=WR_FT_AP_WDS_NOT_WRITTEN;
 s->retry_kind=WR_FT_AP_STOP_RETRY_WDS_NOT_WRITTEN;s->running=0;return 1;
}
static inline int wr_ft_ap_stop_wds_uncertain(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 const struct wr_ft_ap_wds_identity *wds,enum wr_ft_ap_wds_result result)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!serial||
    s->table_serial!=serial||!s->wds_valid||
    !wr_ft_ap_wds_matches(&s->wds,wds)||
    (result!=WR_FT_AP_WDS_PARTIAL&&result!=WR_FT_AP_WDS_UNKNOWN))return 0;
 s->wds_result=result;s->retry_kind=WR_FT_AP_STOP_RETRY_WDS_UNCERTAIN;
 s->running=0;return 1;
}
static inline int wr_ft_ap_stop_wds_resume(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 const struct wr_ft_ap_wds_identity *wds)
{
 if(!wr_ft_ap_stop_matches(s,id)||s->running||!serial||
    s->table_serial!=serial||!s->wds_valid||
    s->retry_kind!=WR_FT_AP_STOP_RETRY_WDS_NOT_WRITTEN||
    s->wds_result!=WR_FT_AP_WDS_NOT_WRITTEN||
    !wr_ft_ap_wds_matches(&s->wds,wds))return 0;
 s->running=1;s->retry_kind=WR_FT_AP_STOP_RETRY_NONE;
 s->wds_retry=1;s->wds_result=WR_FT_AP_WDS_PENDING;return 1;
}
static inline int wr_ft_ap_stop_wds_applied(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 const struct wr_ft_ap_wds_identity *wds)
{
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!serial||
    s->table_serial!=serial||!s->wds_valid||
    !wr_ft_ap_wds_matches(&s->wds,wds)||s->wds_result!=WR_FT_AP_WDS_PENDING)return 0;
 s->wds_result=WR_FT_AP_WDS_APPLIED;return 1;
}
/* Call only after exact software-slot completion and WCID capability closure. */
static inline int wr_ft_ap_stop_wds_complete(struct wr_ft_ap_stop_owner *s,
 const struct wr_ft_ap_stop_identity *id,unsigned long serial,
 const struct wr_ft_ap_wds_identity *wds)
{
 unsigned int i;
 if(!wr_ft_ap_stop_matches(s,id)||!s->running||!serial||
    s->table_serial!=serial||!s->wds_valid||
    !wr_ft_ap_wds_matches(&s->wds,wds)||s->wds_result!=WR_FT_AP_WDS_APPLIED)return 0;
 s->wds_valid=0;s->wds_retry=0;s->wds_result=WR_FT_AP_WDS_PENDING;
 for(i=0;i<6;i++)s->wds.address[i]=0;
 s->wds.device=0;s->wds.generation=0;s->wds.serial=0;s->wds.index=0;s->wds.wcid=0;
 return 1;
}
#endif
