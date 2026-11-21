#include <assert.h>
#include <stdio.h>
#include "ft-ap-cache-reservation.h"
int main(void){
 int device;
 struct wr_ft_ap_stop_identity id={&device,7,9,2,0},foreign=id;
 struct wr_ft_ap_stop_owner ap={0};struct wr_ft_cache_lifetime cache;
 struct wr_ft_cache_lease lease={0};unsigned long serial,ticket;
 wr_ft_cache_lifetime_init(&cache);serial=wr_ft_cache_start(&cache);
 assert(wr_ft_cache_publish(&cache,serial,1));
 assert(wr_ft_cache_enter(&cache,&lease));
 assert(wr_ft_ap_stop_enter(&ap,&id));
 assert(!wr_ft_ap_cache_reserve(&ap,&cache,&id));
 assert(cache.phase==WR_FT_CACHE_DRAINING&&!ap.cache_ticket);
 assert(wr_ft_ap_stop_yield(&ap,&id));
 foreign.bss++;assert(!wr_ft_ap_stop_enter(&ap,&foreign));
 assert(wr_ft_cache_leave(&cache,&lease));
 assert(wr_ft_ap_stop_enter(&ap,&id));
 ticket=wr_ft_ap_cache_reserve(&ap,&cache,&id);assert(ticket);
 assert(ap.cache_ticket==ticket&&cache.owner.serial==ticket);
 assert(wr_ft_ap_stop_advance(&ap,&id,0));
 assert(wr_ft_ap_stop_yield(&ap,&id));
 assert(wr_ft_ap_stop_enter(&ap,&id));
 assert(wr_ft_ap_cache_reserve(&ap,&cache,&id)==ticket);
 assert(!wr_ft_ap_cache_reserve(&ap,&cache,&foreign));
 assert(!wr_ft_ap_cache_destroyed(&ap,&cache,&id));
 assert(wr_ft_cache_destroy_claim(&cache,ticket));
 assert(!wr_ft_ap_cache_destroyed(&ap,&cache,&id));
 assert(!wr_ft_ap_cache_reserve(&ap,&cache,&id));
 assert(wr_ft_cache_destroy_finish(&cache,ticket,1));
 cache.owner.serial++;assert(!wr_ft_ap_cache_destroyed(&ap,&cache,&id));cache.owner.serial--;
 cache.owner.poisoned=1;assert(!wr_ft_ap_cache_destroyed(&ap,&cache,&id));cache.owner.poisoned=0;
 assert(wr_ft_ap_cache_destroyed(&ap,&cache,&id));
 assert(!wr_ft_ap_cache_destroyed(&ap,&cache,&id));
 assert(wr_ft_ap_stop_advance(&ap,&id,2));
 assert(wr_ft_ap_stop_finish(&ap,&id));
 puts("PASS | FT AP/cache reservation | busy drain retry, exact durable ticket reuse, foreign identity refusal, execution claim exclusion; native AP binding pending");return 0;
}
