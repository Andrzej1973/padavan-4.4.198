#if defined(BOARD_WR1200JS)
#include <sys/time.h>
#include "wr-devices/source-collector.h"
#include "wr-devices/snapshot-cache.h"
#include "wr-devices/snapshot-json.h"
#ifndef WR_DEVICE_SOURCE_PATH
#define WR_DEVICE_SOURCE_PATH "/tmp/static_ip.inf"
#endif
#ifndef WR_DEVICE_LOCK_PATH
#define WR_DEVICE_LOCK_PATH "/var/lock/networkmap.lock"
#endif
static struct wr_device_cache wr_device_http_cache;
static char wr_device_http_json[131072];
static struct wr_device_source_paths wr_device_http_paths={WR_DEVICE_SOURCE_PATH,WR_DEVICE_LOCK_PATH};
static void do_wr_devices_json(const char *url,FILE *stream)
{
 struct timeval wall;char epoch[65];uint64_t now,age;size_t length;enum wr_device_cache_state state;
 (void)url;
 if(!wr_device_http_cache.initialized){
  if(gettimeofday(&wall,NULL)){fputs("{\"error\":\"clock_unavailable\"}",stream);return;}
  snprintf(epoch,sizeof(epoch),"httpd-%ld-%ld-%ld",(long)getpid(),(long)wall.tv_sec,(long)wall.tv_usec);
  if(!wr_device_cache_init(&wr_device_http_cache,epoch)){fputs("{\"error\":\"cache_unavailable\"}",stream);return;}
 }
 now=(uint64_t)uptime()*1000;
 state=wr_device_cache_get(&wr_device_http_cache,now,wr_device_networkmap_collect,&wr_device_http_paths);
 if(state==WR_DEVICE_UNAVAILABLE){fputs("{\"error\":\"source_unavailable\"}",stream);return;}
 if(!wr_device_snapshot_json(&wr_device_http_cache.snapshot,wr_device_http_cache.epoch,wr_device_http_cache.sequence,
                             wr_device_http_json,sizeof(wr_device_http_json),&length)||!length){fputs("{\"error\":\"snapshot_unavailable\"}",stream);return;}
 /* Append cache metadata to a successfully serialized object only. */
 wr_device_http_json[length-1]=0;age=now>=wr_device_http_cache.collected_at?now-wr_device_http_cache.collected_at:0;
 fprintf(stream,"%s,\"cacheState\":\"%s\",\"collectionAgeMs\":%llu,\"sourceUpdatedAt\":",wr_device_http_json,
         state==WR_DEVICE_STALE?"stale":"current",(unsigned long long)age);
 if(wr_device_http_cache.snapshot.source_updated_at)fprintf(stream,"%llu",(unsigned long long)wr_device_http_cache.snapshot.source_updated_at);
 else fputs("null",stream);
 fputc('}',stream);
}
#endif
