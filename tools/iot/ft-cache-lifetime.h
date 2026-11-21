/* Prepared only. All state transitions require the SAME adapter lifetime lock,
 * which must outlive the native cache lock. Never wait or call native init/free
 * while holding that lock. Adapter allocation lifetime is an external contract.
 * Leases are linear, noncopyable caller-owned objects. Init only on fresh memory.
 */
#ifndef WR_FT_CACHE_LIFETIME_H
#define WR_FT_CACHE_LIFETIME_H
#include "peer-table-owner.h"
enum wr_ft_cache_phase { WR_FT_CACHE_COLD, WR_FT_CACHE_STARTING,
 WR_FT_CACHE_LIVE, WR_FT_CACHE_DRAINING, WR_FT_CACHE_DESTROYING,
 WR_FT_CACHE_FREEING };
struct wr_ft_cache_lifetime {
 struct wr_iot_peer_table_owner owner;
 enum wr_ft_cache_phase phase;
};
struct wr_ft_cache_lease {
 struct wr_ft_cache_lifetime *cache;
 unsigned long serial;
};
static inline void wr_ft_cache_lifetime_init(struct wr_ft_cache_lifetime *s)
{
 wr_iot_peer_table_owner_init(&s->owner);
 s->owner.closed=1;s->phase=WR_FT_CACHE_COLD;
}
/* Native init follows outside the lifetime lock, under this exclusive ticket. */
static inline unsigned long wr_ft_cache_start(struct wr_ft_cache_lifetime *s)
{
 unsigned long serial;
 if(!s||s->phase!=WR_FT_CACHE_COLD)return 0;
 serial=wr_iot_peer_table_begin_open(&s->owner);
 if(serial)s->phase=WR_FT_CACHE_STARTING;
 return serial;
}
/* Report success only once native lock/lists are fully initialized. Uncertain
 * or partial init retains ownership; it must not publish or retry native init. */
static inline int wr_ft_cache_publish(struct wr_ft_cache_lifetime *s,
 unsigned long serial,int initialized)
{
 if(!s||s->phase!=WR_FT_CACHE_STARTING||!serial||
    !wr_iot_peer_table_allows(&s->owner,serial))return 0;
 if(initialized!=1){s->owner.poisoned=1;return 0;}
 if(!wr_iot_peer_table_finish(&s->owner,serial,1))return 0;
 s->phase=WR_FT_CACHE_LIVE;return 1;
}
static inline int wr_ft_cache_enter(struct wr_ft_cache_lifetime *s,
 struct wr_ft_cache_lease *lease)
{
 if(!s||!lease||lease->cache||lease->serial||s->phase!=WR_FT_CACHE_LIVE||
    !wr_iot_peer_table_transaction_enter(&s->owner))return 0;
 lease->cache=s;lease->serial=s->owner.serial;return 1;
}
static inline int wr_ft_cache_leave(struct wr_ft_cache_lifetime *s,
 struct wr_ft_cache_lease *lease)
{
 if(!s||!lease||lease->cache!=s||!lease->serial||
    lease->serial!=s->owner.serial||
    (s->phase!=WR_FT_CACHE_LIVE&&s->phase!=WR_FT_CACHE_DRAINING))return 0;
 if(!wr_iot_peer_table_transaction_leave(&s->owner))return 0;
 lease->cache=0;lease->serial=0;return 1;
}
/* Close ingress immediately even when holders remain. Caller drops lifetime
 * lock and waits/retries; timeout never authorizes freeing native cache. */
static inline int wr_ft_cache_close(struct wr_ft_cache_lifetime *s)
{
 if(!s||s->owner.poisoned||s->owner.retained||s->owner.active||
    (s->phase!=WR_FT_CACHE_LIVE&&s->phase!=WR_FT_CACHE_DRAINING))return 0;
 s->owner.closed=1;s->phase=WR_FT_CACHE_DRAINING;return 1;
}
static inline unsigned long wr_ft_cache_destroy_begin(struct wr_ft_cache_lifetime *s)
{
 unsigned long serial;
 if(!s||s->phase!=WR_FT_CACHE_DRAINING||!s->owner.closed)return 0;
 serial=wr_iot_peer_table_begin_open(&s->owner);
 if(serial){s->owner.closed=1;s->phase=WR_FT_CACHE_DESTROYING;}
 return serial;
}
/* Exactly one executor may consume the reserved serial. Other callers must
 * not touch native cache state while this phase is active. */
static inline int wr_ft_cache_destroy_claim(struct wr_ft_cache_lifetime *s,
 unsigned long serial)
{
 if(!s||!serial||s->phase!=WR_FT_CACHE_DESTROYING||!s->owner.active||
    s->owner.serial!=serial||s->owner.transactions||s->owner.poisoned||
    s->owner.retained||!s->owner.closed)return 0;
 s->phase=WR_FT_CACHE_FREEING;return 1;
}
/* Native destroy completed outside lifetime lock. No late holder may touch the
 * freed native lock. Keep ticket exclusive until completion is confirmed. */
static inline int wr_ft_cache_destroy_finish(struct wr_ft_cache_lifetime *s,
 unsigned long serial,int destroyed)
{
 if(!s||s->phase!=WR_FT_CACHE_FREEING||!serial||
    !s->owner.active||s->owner.serial!=serial||s->owner.transactions||
    s->owner.poisoned||s->owner.retained)return 0;
 if(destroyed!=1){s->owner.poisoned=1;return 0;}
 s->owner.active=0;s->owner.closed=1;s->phase=WR_FT_CACHE_COLD;return 1;
}
#endif
