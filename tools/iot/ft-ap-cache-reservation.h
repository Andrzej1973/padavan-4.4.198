/* Prepared only. Caller holds ONE adapter lifetime lock over both records.
 * Device/generation/operation provenance remains the caller's responsibility. */
#ifndef WR_FT_AP_CACHE_RESERVATION_H
#define WR_FT_AP_CACHE_RESERVATION_H
#include "ft-ap-stop-owner.h"
#include "ft-cache-lifetime.h"
static inline unsigned long wr_ft_ap_cache_reserve(
 struct wr_ft_ap_stop_owner *ap,struct wr_ft_cache_lifetime *cache,
 const struct wr_ft_ap_stop_identity *id)
{
 unsigned long ticket;
 if(!ap||!cache||!wr_ft_ap_stop_matches(ap,id)||!ap->running)return 0;
 if(ap->cache_ticket){
  if(cache->phase!=WR_FT_CACHE_DESTROYING||!cache->owner.active||
     cache->owner.serial!=ap->cache_ticket||cache->owner.transactions||
     cache->owner.poisoned||cache->owner.retained||!cache->owner.closed)return 0;
  return ap->cache_ticket;
 }
 if(ap->stage||!wr_ft_cache_close(cache))return 0;
 ticket=wr_ft_cache_destroy_begin(cache);
 if(!ticket)return 0;
 if(!wr_ft_ap_stop_bind(ap,id,ticket)){
  cache->owner.poisoned=1;return 0;
 }
 return ticket;
}
/* Stage1 is the caller's pre-cache checkpoint. Advance only on the exact
 * completed destroy, never on a reserved or merely claimed serial. */
static inline int wr_ft_ap_cache_destroyed(
 struct wr_ft_ap_stop_owner *ap,const struct wr_ft_cache_lifetime *cache,
 const struct wr_ft_ap_stop_identity *id)
{
 if(!ap||!cache||!wr_ft_ap_stop_matches(ap,id)||!ap->running||
    ap->stage!=1||!ap->cache_ticket||cache->owner.serial!=ap->cache_ticket||
    cache->phase!=WR_FT_CACHE_COLD||!cache->owner.closed||
    cache->owner.active||cache->owner.transactions||cache->owner.poisoned||
    cache->owner.retained)return 0;
 return wr_ft_ap_stop_advance(ap,id,1);
}
#endif
