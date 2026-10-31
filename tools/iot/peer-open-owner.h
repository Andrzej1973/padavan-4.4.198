/* Candidate protocol only. All accesses hold MacTabLock. Adapter/netdevice
 * lifetime and transport of tickets are caller obligations, not proved here. */
#ifndef WR_IOT_PEER_OPEN_OWNER_H
#define WR_IOT_PEER_OPEN_OWNER_H
#include "peer-table-owner.h"
enum wr_iot_peer_open_phase {WR_PEER_OPEN_IDLE,WR_PEER_OPEN_CONFIG,
 WR_PEER_OPEN_STARTUP,WR_PEER_OPEN_RETAINED};
struct wr_iot_peer_open_owner {
 const void *device;
 unsigned long serial,next_lease,active_lease;
 unsigned int phase,lease_admitted;
};
struct wr_iot_peer_open_ticket {const void *device;unsigned long serial;};
static inline void wr_iot_peer_open_owner_init(struct wr_iot_peer_open_owner *s){
 s->device=0;s->serial=0;s->next_lease=0;s->active_lease=0;s->phase=WR_PEER_OPEN_IDLE;s->lease_admitted=0;
}
static inline int wr_iot_peer_open_matches(const struct wr_iot_peer_open_owner *s,
 const struct wr_iot_peer_table_owner *table,const struct wr_iot_peer_open_ticket *t){
 return s&&table&&t&&t->device&&t->serial&&s->device==t->device&&s->serial==t->serial&&
  wr_iot_peer_table_allows(table,t->serial);
}
/* Caller verifies table empty/ready in this SAME critical section. */
static inline int wr_iot_peer_open_begin(struct wr_iot_peer_open_owner *s,
 struct wr_iot_peer_table_owner *table,const void *device,int ready,
 struct wr_iot_peer_open_ticket *ticket){
 unsigned long serial;
 if(!s||!table||!device||!ticket||!ready||s->phase!=WR_PEER_OPEN_IDLE)return 0;
 serial=wr_iot_peer_table_begin_open(table);if(!serial)return 0;
 s->device=device;s->serial=serial;s->phase=WR_PEER_OPEN_CONFIG;
 ticket->device=device;ticket->serial=serial;return 1;
}
static inline int wr_iot_peer_open_startup(struct wr_iot_peer_open_owner *s,
 const struct wr_iot_peer_table_owner *table,const struct wr_iot_peer_open_ticket *t){
 if(!wr_iot_peer_open_matches(s,table,t)||s->phase!=WR_PEER_OPEN_CONFIG)return 0;
 s->phase=WR_PEER_OPEN_STARTUP;return 1;
}
/* An explicit startup caller may claim one insertion. Normal callers must
 * still use table_allows(table,0), which remains false throughout startup. */
static inline unsigned long wr_iot_peer_open_insert_begin(struct wr_iot_peer_open_owner *s,
 struct wr_iot_peer_table_owner *table,const struct wr_iot_peer_open_ticket *t){
 if(!wr_iot_peer_open_matches(s,table,t)||s->phase!=WR_PEER_OPEN_STARTUP||s->active_lease)return 0;
 if(s->next_lease==~0UL){
  (void)wr_iot_peer_table_finish(table,t->serial,0);s->phase=WR_PEER_OPEN_RETAINED;return 0;
 }
 s->lease_admitted=0;s->active_lease=++s->next_lease;return s->active_lease;
}
static inline int wr_iot_peer_open_insert_admit(struct wr_iot_peer_open_owner *s,
 const struct wr_iot_peer_table_owner *table,const struct wr_iot_peer_open_ticket *t,
 unsigned long lease){
 if(!lease||!wr_iot_peer_open_matches(s,table,t)||s->phase!=WR_PEER_OPEN_STARTUP||
    s->active_lease!=lease||s->lease_admitted)return 0;
 s->lease_admitted=1;return 1;
}
static inline int wr_iot_peer_open_insert_end(struct wr_iot_peer_open_owner *s,
 const struct wr_iot_peer_table_owner *table,const struct wr_iot_peer_open_ticket *t,
 unsigned long lease){
 /* A failed open may retain while its admitted insertion is still running.
  * Exact completion may drop the lease, never the retained table ownership. */
 if(!s||!table||!t||!lease||s->device!=t->device||s->serial!=t->serial||
    table->serial!=t->serial||!table->active||s->active_lease!=lease||
    (s->phase!=WR_PEER_OPEN_STARTUP&&s->phase!=WR_PEER_OPEN_RETAINED))return 0;
 s->active_lease=0;s->lease_admitted=0;return 1;
}
static inline int wr_iot_peer_open_finish(struct wr_iot_peer_open_owner *s,
 struct wr_iot_peer_table_owner *table,const struct wr_iot_peer_open_ticket *t,int success){
 if(!wr_iot_peer_open_matches(s,table,t)||
    (s->phase!=WR_PEER_OPEN_CONFIG&&s->phase!=WR_PEER_OPEN_STARTUP))return 0;
 if(success&&(s->phase!=WR_PEER_OPEN_STARTUP||s->active_lease))return 0;
 if(!wr_iot_peer_table_finish(table,t->serial,success))return 0;
 if(!success){s->phase=WR_PEER_OPEN_RETAINED;return 1;}
 s->device=0;s->serial=0;s->phase=WR_PEER_OPEN_IDLE;return 1;
}
#endif
