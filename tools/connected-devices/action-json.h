#ifndef WR_ACTION_JSON_H
#define WR_ACTION_JSON_H
#include "action-drain.h"
#include "snapshot-json.h"
/* Sessions and cumulative counters are strings: a 64-bit session must not
 * lose identity through JavaScript floating point. No inferred roam outcome. */
static inline int wr_action_json(const struct wr_action_log *log,char *data,
 size_t capacity,size_t *length){
 struct wr_device_json_buffer out={data,capacity,0};size_t i;
 if(length)*length=0;
 if(!log||!data||!length||!capacity||log->count>WR_ACTION_RING_MAX||log->first>=WR_ACTION_RING_MAX)return 0;
 data[0]=0;
 if(!wr_device_json_format(&out,"{\"ownerAvailable\":%s,\"dropped\":\"%llu\",\"rejected\":\"%llu\",\"missing\":\"%llu\",\"events\":[",
 log->owner_available?"true":"false",(unsigned long long)log->dropped,(unsigned long long)log->rejected,(unsigned long long)log->session.missing))return 0;
 for(i=0;i<log->count;i++){
  const struct wr_action_event *e=&log->events[(log->first+i)%WR_ACTION_RING_MAX];const char *stage;
  if(!wr_action_valid(e)||e->source!=WR_ACTION_STEERING)return 0;
  if(e->stage==WR_ACTION_INTENT)stage="intent";
  else if(e->stage==WR_ACTION_IOCTL_ACCEPTED)stage="ioctl_accepted";
  else if(e->stage==WR_ACTION_IOCTL_FAILED)stage="ioctl_failed";
  else if(e->stage==WR_ACTION_DRIVER_ACK)stage="driver_ack";else return 0;
  if((i&&!wr_device_json_append(&out,","))||!wr_device_json_format(&out,
  "{\"session\":\"%016llx\",\"sequence\":%llu,\"uptimeMs\":%llu,\"mac\":\"%02X:%02X:%02X:%02X:%02X:%02X\",\"radio\":%u,\"bss\":%u,\"cookie\":%u,\"operation\":\"%s\",\"stage\":\"%s\",\"result\":%d,\"outcome\":\"unknown\"}",
  (unsigned long long)e->session,(unsigned long long)e->sequence,(unsigned long long)e->uptime_ms,
  e->mac[0],e->mac[1],e->mac[2],e->mac[3],e->mac[4],e->mac[5],e->radio,e->bss,e->cookie,
  e->operation==WR_ACTION_ALLOW?"allow":"remove_candidate",stage,e->result))return 0;
 }
 if(!wr_device_json_append(&out,"]}"))return 0;
 *length=out.length;return 1;
}
#endif
