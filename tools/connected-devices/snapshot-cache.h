/* Process-wide RAM cache for the pinned single-event-loop httpd.
 * Collector must read consistent passive sources; now is monotonic milliseconds. */
#ifndef WR_DEVICE_SNAPSHOT_CACHE_H
#define WR_DEVICE_SNAPSHOT_CACHE_H
#include "networkmap.h"
#include <stdint.h>
enum wr_device_cache_state {WR_DEVICE_UNAVAILABLE=0,WR_DEVICE_CURRENT=1,WR_DEVICE_STALE=2};
struct wr_device_cache {
 struct wr_device_snapshot snapshot;char epoch[65];uint64_t sequence,attempt_at,collected_at,collections;
 int initialized,attempted,has_data,last_failed;
};
static inline int wr_device_cache_init(struct wr_device_cache *cache,const char *epoch){
 size_t n;if(!cache||!epoch||(n=strnlen(epoch,65))==0||n>64)return 0;
 memset(cache,0,sizeof(*cache));memcpy(cache->epoch,epoch,n);cache->initialized=1;return 1;
}
static inline int wr_device_snapshot_valid(const struct wr_device_snapshot *snapshot){
 unsigned int i;if(snapshot->count>WR_DEVICE_LIMIT)return 0;
 for(i=0;i<snapshot->count;i++){
  const struct wr_device_record *r=&snapshot->records[i];
  if(strnlen(r->ip,sizeof(r->ip))==sizeof(r->ip)||strnlen(r->mac,sizeof(r->mac))==sizeof(r->mac)||strnlen(r->name,sizeof(r->name))==sizeof(r->name))return 0;
 }
 return 1;
}
static inline int wr_device_snapshot_same(const struct wr_device_snapshot *a,const struct wr_device_snapshot *b){
 unsigned int i;
 if(a->count!=b->count||a->invalid!=b->invalid||!!a->truncated!=!!b->truncated)return 0;
 for(i=0;i<a->count;i++){
  const struct wr_device_record *x=&a->records[i],*y=&b->records[i];
  if(strcmp(x->ip,y->ip)||strcmp(x->mac,y->mac)||strcmp(x->name,y->name)||x->legacy_type!=y->legacy_type||!!x->http!=!!y->http||!!x->networkmap_stale!=!!y->networkmap_stale)return 0;
 }
 return 1;
}
static inline enum wr_device_cache_state wr_device_cache_get(struct wr_device_cache *cache,uint64_t now,int (*collect)(struct wr_device_snapshot *,void *),void *context){
 struct wr_device_snapshot candidate;int changed;
 if(!cache||!cache->initialized||!collect)return WR_DEVICE_UNAVAILABLE;
 if(cache->attempted&&now>=cache->attempt_at&&now-cache->attempt_at<5000)
  return cache->has_data?(cache->last_failed?WR_DEVICE_STALE:WR_DEVICE_CURRENT):WR_DEVICE_UNAVAILABLE;
 cache->attempted=1;cache->attempt_at=now;cache->collections++;memset(&candidate,0,sizeof(candidate));
 if(!collect(&candidate,context)||!wr_device_snapshot_valid(&candidate)){
  cache->last_failed=1;return cache->has_data?WR_DEVICE_STALE:WR_DEVICE_UNAVAILABLE;
 }
 changed=!cache->has_data||!wr_device_snapshot_same(&candidate,&cache->snapshot);
 if(changed&&cache->sequence==9007199254740991ULL){cache->last_failed=1;return cache->has_data?WR_DEVICE_STALE:WR_DEVICE_UNAVAILABLE;}
 if(changed){cache->snapshot=candidate;cache->sequence++;}
 cache->has_data=1;cache->last_failed=0;cache->collected_at=now;
 return WR_DEVICE_CURRENT;
}
#endif
