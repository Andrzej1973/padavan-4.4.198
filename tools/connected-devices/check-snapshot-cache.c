#define _GNU_SOURCE
#include "snapshot-cache.h"
#include <assert.h>
static struct wr_device_cache cache;
static int calls,failure,version;
static int collect(struct wr_device_snapshot *out,void *context){
 assert(context==&calls);calls++;if(failure)return 0;
 out->count=1;strcpy(out->records[0].ip,"192.168.1.2");strcpy(out->records[0].mac,"00:11:22:33:44:55");strcpy(out->records[0].name,version?"changed":"initial");return 1;
}
int main(void){uint64_t sequence;
 assert(!wr_device_cache_init(&cache,""));assert(wr_device_cache_init(&cache,"httpd-instance-A"));
 assert(wr_device_cache_get(&cache,0,collect,&calls)==WR_DEVICE_CURRENT&&calls==1&&cache.sequence==1);
 assert(wr_device_cache_get(&cache,1,collect,&calls)==WR_DEVICE_CURRENT&&calls==1);
 assert(wr_device_cache_get(&cache,4999,collect,&calls)==WR_DEVICE_CURRENT&&calls==1);
 assert(wr_device_cache_get(&cache,5000,collect,&calls)==WR_DEVICE_CURRENT&&calls==2&&cache.sequence==1); // Same source, stable serial.
 sequence=cache.sequence;failure=1;assert(wr_device_cache_get(&cache,10000,collect,&calls)==WR_DEVICE_STALE&&cache.sequence==sequence&&calls==3);
 assert(wr_device_cache_get(&cache,10001,collect,&calls)==WR_DEVICE_STALE&&calls==3);assert(!strcmp(cache.snapshot.records[0].name,"initial"));
 failure=0;version=1;assert(wr_device_cache_get(&cache,15000,collect,&calls)==WR_DEVICE_CURRENT&&cache.sequence==2&&calls==4);
 assert(wr_device_cache_get(&cache,1000,collect,&calls)==WR_DEVICE_CURRENT&&calls==5); // Clock rollback expires prior deadline.
 assert(wr_device_cache_init(&cache,"httpd-instance-B")&&cache.sequence==0&&!cache.has_data);
 failure=1;assert(wr_device_cache_get(&cache,0,collect,&calls)==WR_DEVICE_UNAVAILABLE);
 assert(wr_device_cache_get(&cache,1,collect,&calls)==WR_DEVICE_UNAVAILABLE&&calls==6);
 puts("PASS shared RAM snapshot cache: five-second collection bound, stable unchanged sequence, stale retention, retry recovery and epoch reset");return 0;
}
