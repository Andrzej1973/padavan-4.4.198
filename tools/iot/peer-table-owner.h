/* All accesses require the adapter's MacTabLock. Initialize only on a fresh
 * adapter, outside MacTab memory. No waiting/freeing or recovery is done here. */
#ifndef WR_IOT_PEER_TABLE_OWNER_H
#define WR_IOT_PEER_TABLE_OWNER_H
struct wr_iot_peer_table_owner {
 unsigned long serial;
 unsigned int active,retained,poisoned,transactions,closed;
};
static inline void wr_iot_peer_table_owner_init(struct wr_iot_peer_table_owner *s){
 s->serial=0;s->active=0;s->retained=0;s->poisoned=0;s->transactions=0;s->closed=0;
}
static inline int wr_iot_peer_table_allows(const struct wr_iot_peer_table_owner *s,
 unsigned long serial){
 if(!s||s->retained||s->poisoned||s->closed)return 0;
 if(!serial)return !s->active;
 return s->active&&s->serial==serial;
}
static inline unsigned long wr_iot_peer_table_begin(struct wr_iot_peer_table_owner *s){
 if(!wr_iot_peer_table_allows(s,0)||s->transactions)return 0;
 if(s->serial==~0UL){s->poisoned=1;return 0;}
 s->serial++;s->active=1;return s->serial;
}
static inline int wr_iot_peer_table_finish(struct wr_iot_peer_table_owner *s,
 unsigned long serial,int success){
 if(!serial||!wr_iot_peer_table_allows(s,serial))return 0;
 if(success)s->active=0;
 else s->retained=1;
 return 1;
}
/* Reopen alone can consume a completed-close seal. Caller checks table empty
 * and physical admission in the same lock/lifetime transaction. */
static inline unsigned long wr_iot_peer_table_begin_open(struct wr_iot_peer_table_owner *s){
 unsigned long serial;
 unsigned int closed;
 if(!s||s->active||s->retained||s->poisoned||s->transactions)return 0;
 closed=s->closed;s->closed=0;serial=wr_iot_peer_table_begin(s);
 if(!serial)s->closed=closed;
 return serial;
}
static inline int wr_iot_peer_table_close_seal(struct wr_iot_peer_table_owner *s,unsigned long serial){
 if(!wr_iot_peer_table_finish(s,serial,1))return 0;
 s->closed=1;return 1;
}
/* Synchronous callers balance enter/leave exactly once. Not an asynchronous
 * completion token. Existing transactions may coexist, exclusive reset may not. */
static inline int wr_iot_peer_table_transaction_enter(struct wr_iot_peer_table_owner *s){
 if(!wr_iot_peer_table_allows(s,0))return 0;
 if(s->transactions==~0U){s->poisoned=1;return 0;}
 s->transactions++;return 1;
}
static inline int wr_iot_peer_table_transaction_leave(struct wr_iot_peer_table_owner *s){
 if(!s||!s->transactions){if(s)s->poisoned=1;return 0;}
 s->transactions--;return !s->poisoned;
}
#endif
