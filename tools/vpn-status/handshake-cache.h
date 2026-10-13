#ifndef WR_HANDSHAKE_CACHE_H
#define WR_HANDSHAKE_CACHE_H
#include "handshake-observation.h"
enum wr_handshake_cache_state {WR_HS_UNKNOWN,WR_HS_CURRENT,WR_HS_STALE};
struct wr_handshake_cache {
 struct wr_handshake_observation observation;
 uint64_t sampled_at;
 int has_sample,last_attempt_ok;
};
/* Caller supplies monotonic seconds, never NTP-adjusted wall time. */
static inline void wr_handshake_cache_publish(struct wr_handshake_cache *cache,
 uint64_t now,int success,const struct wr_handshake_observation *observation)
{
 if(!cache)return;
 if(cache->has_sample && now<cache->sampled_at)memset(cache,0,sizeof(*cache));
 cache->last_attempt_ok=success && observation;
 if(cache->last_attempt_ok){cache->observation=*observation;cache->sampled_at=now;cache->has_sample=1;}
}
static inline enum wr_handshake_cache_state wr_handshake_cache_get(
 const struct wr_handshake_cache *cache,uint64_t now,uint64_t max_age,uint64_t *age)
{
 if(age)*age=0;
 if(!cache || !cache->has_sample || now<cache->sampled_at)return WR_HS_UNKNOWN;
 if(age)*age=now-cache->sampled_at;
 if(!cache->last_attempt_ok || now-cache->sampled_at>max_age)return WR_HS_STALE;
 return WR_HS_CURRENT;
}
#endif
