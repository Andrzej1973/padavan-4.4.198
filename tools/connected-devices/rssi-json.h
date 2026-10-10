#ifndef WR_RSSI_JSON_H
#define WR_RSSI_JSON_H
#include "rssi-collector.h"
#include "snapshot-json.h"
/* All 64-bit values are strings. Stages describe driver observations, never
 * delivery acknowledgements or a successful roam. */
static inline int wr_rssi_json(const struct wr_rssi_collector *c,char *data,
 size_t capacity,size_t *length)
{
 struct wr_device_json_buffer out={data,capacity,0};unsigned int i,first;
 if(length)*length=0;
 if(!c||!data||!length||!capacity||c->history.count>256||c->history.next>=256)return 0;
 data[0]=0;
 if(!wr_device_json_format(&out,"{\"cacheState\":\"%s\",\"evicted\":\"%llu\",\"radios\":[",
  c->health[0].available&&c->health[1].available?"current":c->history.count?"stale":"unavailable",c->history.evicted))return 0;
 for(i=0;i<2;i++) {
  const struct wr_rssi_collector_health *h=&c->health[i];
  const struct wr_rssi_history_radio *r=&c->history.radios[i];
  if(!wr_device_json_format(&out,"%s{\"radio\":%u,\"available\":%s,\"attempted\":%s,\"error\":%d,\"failures\":\"%llu\",\"recoveries\":\"%llu\",\"lastSuccessMs\":\"%llu\",\"missing\":\"%llu\",\"restarts\":\"%llu\",\"driverOverwritten\":\"%llu\"}",
   i?",":"",i,h->available?"true":"false",h->attempted?"true":"false",h->error,
   h->failures,h->recoveries,h->last_success_ms,r->missing,r->restarts,r->driver_overwritten))return 0;
 }
 if(!wr_device_json_append(&out,"],\"events\":["))return 0;
 first=(c->history.next+256-c->history.count)%256;
 for(i=0;i<c->history.count;i++) {
  const struct wr_rssi_history_event *e=&c->history.events[(first+i)%256];
  const struct wr_rssi_record *r=&e->record;unsigned char scratch[32];const char *stage;
  if((!e->session[0]&&!e->session[1])||!wr_rssi_query_record_encode(scratch,32,r))return 0;
  switch(r->stage) {
   case 1:stage="decision";break;
   case 2:stage="allocation_failed";break;
   case 3:stage="frame_submitted";break;
   case 4:stage="entry_cleared";break;
   default:return 0;
  }
  if(!wr_device_json_format(&out,"%s{\"session\":\"%016llx%016llx\",\"sequence\":\"%llu\",\"uptimeMs\":\"%llu\",\"attempt\":%u,\"mac\":\"%02X:%02X:%02X:%02X:%02X:%02X\",\"radio\":%u,\"bss\":%u,\"stage\":\"%s\",\"outcome\":\"unknown\"}",
   i?",":"",e->session[0],e->session[1],r->sequence,r->uptime_ms,r->attempt,
   r->mac[0],r->mac[1],r->mac[2],r->mac[3],r->mac[4],r->mac[5],r->radio,r->bss,stage))return 0;
 }
 if(!wr_device_json_append(&out,"]}"))return 0;
 *length=out.length;return 1;
}
#endif
