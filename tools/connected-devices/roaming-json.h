#ifndef WR_ROAM_JSON_H
#define WR_ROAM_JSON_H
#include "roaming-history.h"
#include "snapshot-json.h"
/* Chronological RAM history. A band change is an observation, not causation. */
static inline int wr_roam_json(const struct wr_roam_history *h,const char *epoch,
 char *data,size_t capacity,size_t *length){
 struct wr_device_json_buffer out={data,capacity,0};unsigned int i,start;
 if(length)*length=0;
 if(!h||!epoch||!data||!length||!capacity||h->event_count>WR_ROAM_EVENTS||h->next>=WR_ROAM_EVENTS)return 0;
 data[0]=0;
 if(!wr_device_json_append(&out,"{\"epoch\":")||!wr_device_json_string(&out,epoch,64)||
 !wr_device_json_format(&out,",\"dropped\":%u,\"clientDropped\":%u,\"clientEvictions\":%u,\"gap\":%s,\"events\":[",h->dropped,h->client_dropped,h->client_evictions,h->gap?"true":"false"))return 0;
 start=(h->next+WR_ROAM_EVENTS-h->event_count)%WR_ROAM_EVENTS;
 for(i=0;i<h->event_count;i++){
  const struct wr_roam_event *e=&h->events[(start+i)%WR_ROAM_EVENTS];const char *kind;
  if(e->kind==WR_ROAM_OBSERVED)kind="observed";
  else if(e->kind==WR_ROAM_BAND_CHANGE)kind="band_change";
  else if(e->kind==WR_ROAM_AMBIGUOUS)kind="ambiguous";
  else if(e->kind==WR_ROAM_GAP)kind="gap";else return 0;
  if(e->before>3||e->after>3||e->sequence>9007199254740991ULL||e->time_ms>9007199254740991ULL)return 0;
  if((i&&!wr_device_json_append(&out,","))||!wr_device_json_format(&out,"{\"sequence\":%llu,\"uptimeMs\":%llu,\"kind\":\"%s\",\"mac\":",(unsigned long long)e->sequence,(unsigned long long)e->time_ms,kind)||!wr_device_json_string(&out,e->mac,17)||!wr_device_json_format(&out,",\"before\":%u,\"after\":%u,\"cause\":\"unknown\"}",e->before,e->after))return 0;
 }
 if(!wr_device_json_append(&out,"]}"))return 0;
 *length=out.length;return 1;
}
#endif
