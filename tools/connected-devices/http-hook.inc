#if defined(BOARD_WR1200JS)
#include <sys/time.h>
#include "wr-devices/source-collector.h"
#include "wr-devices/snapshot-cache.h"
#include "wr-devices/snapshot-json.h"
#include "wr-devices/roaming-history.h"
#include "wr-devices/roaming-json.h"
#include "wr-devices/action-runtime.h"
#include "wr-devices/action-json.h"
static char wr_device_http_action_json[65536];
static struct wr_action_runtime wr_device_http_actions;
#ifndef WR_DEVICE_SOURCE_PATH
#define WR_DEVICE_SOURCE_PATH "/tmp/static_ip.inf"
#endif
#ifndef WR_DEVICE_LOCK_PATH
#define WR_DEVICE_LOCK_PATH "/var/lock/networkmap.lock"
#endif
static struct wr_device_cache wr_device_http_cache;
static struct wr_roam_history wr_device_http_history;
static char wr_device_http_json[131072];
static struct wr_device_source_paths wr_device_http_paths={WR_DEVICE_SOURCE_PATH,WR_DEVICE_LOCK_PATH};
extern int wr_device_collect_radio(struct wr_device_snapshot *networkmap);
static int wr_device_http_collect(struct wr_device_snapshot *snapshot,void *context)
{
 if(!wr_device_networkmap_collect(snapshot,context))return 0;
 return wr_device_collect_radio(snapshot);
}
static enum wr_device_cache_state wr_device_http_update(void)
{
 struct timeval wall;char epoch[65];uint64_t now;enum wr_device_cache_state state;
 if(!wr_device_http_cache.initialized){
  if(gettimeofday(&wall,NULL))return WR_DEVICE_UNAVAILABLE;
  snprintf(epoch,sizeof(epoch),"httpd-%ld-%ld-%ld",(long)getpid(),(long)wall.tv_sec,(long)wall.tv_usec);
  if(!wr_device_cache_init(&wr_device_http_cache,epoch))return WR_DEVICE_UNAVAILABLE;
 }
 now=(uint64_t)uptime()*1000;
 state=wr_device_cache_get(&wr_device_http_cache,now,wr_device_http_collect,&wr_device_http_paths);
 if(state==WR_DEVICE_CURRENT)
  wr_roam_observe(&wr_device_http_history,&wr_device_http_cache.snapshot,wr_device_http_cache.collected_at,1);
 else wr_roam_observe(&wr_device_http_history,NULL,now,0);
 return state;
}
void wr_device_background_tick(void){(void)wr_device_http_update();wr_action_runtime_tick(&wr_device_http_actions,(uint64_t)uptime()*1000);}
static void do_wr_roaming_json(const char *url,FILE *stream)
{
 size_t length,action_length;enum wr_device_cache_state state;(void)url;
 state=wr_device_http_update();
 if(!wr_device_http_cache.initialized || !wr_roam_json(&wr_device_http_history,
 wr_device_http_cache.epoch,wr_device_http_json,sizeof(wr_device_http_json),&length)){
  fputs("{\"error\":\"history_unavailable\"}",stream);return;
 }
 if(!wr_action_json(&wr_device_http_actions.log,wr_device_http_action_json,sizeof(wr_device_http_action_json),&action_length)){fputs("{\"error\":\"actions_unavailable\"}",stream);return;}
 /* A stale source does not erase history. Expose its current validity. */
 wr_device_http_json[length-1]=0;
 fprintf(stream,"%s,\"cacheState\":\"%s\",\"serverUptimeMs\":%llu,\"actions\":%s}",wr_device_http_json,
 state==WR_DEVICE_CURRENT?"current":state==WR_DEVICE_STALE?"stale":"unavailable",
 (unsigned long long)((uint64_t)uptime()*1000),wr_device_http_action_json);
}
static void do_wr_devices_json(const char *url,FILE *stream)
{
 uint64_t now,age;size_t length;enum wr_device_cache_state state;
 (void)url;
 state=wr_device_http_update();now=(uint64_t)uptime()*1000;
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
