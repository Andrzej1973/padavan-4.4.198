#ifndef WR_DEVICE_ROAMING_HISTORY_H
#define WR_DEVICE_ROAMING_HISTORY_H
#include "networkmap.h"
#define WR_ROAM_EVENTS 256
enum wr_roam_kind { WR_ROAM_OBSERVED=1, WR_ROAM_BAND_CHANGE, WR_ROAM_AMBIGUOUS, WR_ROAM_GAP };
struct wr_roam_event {uint64_t time_ms,sequence;char mac[18];unsigned char kind,before,after;};
struct wr_roam_client {char mac[18];unsigned char band,pending,confirmations,seen;};
struct wr_roam_history {
 struct wr_roam_client clients[WR_DEVICE_LIMIT];
 struct wr_roam_event events[WR_ROAM_EVENTS];
 unsigned int count,next,event_count,dropped;
 uint64_t sequence,last_ms;int has_sample,gap;
};
static inline void wr_roam_event_add(struct wr_roam_history *h,uint64_t now,
 const char *mac,int kind,int before,int after){
 struct wr_roam_event *e=&h->events[h->next];
 memset(e,0,sizeof(*e));e->time_ms=now;e->sequence=++h->sequence;
 if(mac)memcpy(e->mac,mac,18);
 e->kind=kind;e->before=before;e->after=after;
 h->next=(h->next+1)%WR_ROAM_EVENTS;
 if(h->event_count<WR_ROAM_EVENTS)h->event_count++;else h->dropped++;
}
/* Successful associated-client snapshots only. No driver action or causal claim.
 * Caller must schedule collection independently of browser visibility. */
static inline int wr_roam_observe(struct wr_roam_history *h,
 const struct wr_device_snapshot *snapshot,uint64_t now,int source_valid){
 unsigned int i,j;int discontinuity;
 if(!h)return 0;
 if(source_valid){
  if(!snapshot||snapshot->count>WR_DEVICE_LIMIT)return 0;
  for(i=0;i<snapshot->count;i++){
   const struct wr_device_record *r=&snapshot->records[i];
   if(strnlen(r->mac,sizeof(r->mac))==sizeof(r->mac)||r->radio.band_mask>3)return 0;
  }
 }
 if(source_valid&&h->has_sample&&!h->gap&&now==h->last_ms)return 1;
 discontinuity=!source_valid||(h->has_sample&&(now<h->last_ms||now-h->last_ms>10000));
 if(discontinuity){
  if(!h->gap)wr_roam_event_add(h,now,NULL,WR_ROAM_GAP,0,0);
  h->gap=1;
  for(i=0;i<h->count;i++){h->clients[i].band=0;h->clients[i].pending=0;h->clients[i].confirmations=0;}
 }
 if(!source_valid)return 1;
 /* Truncation cannot establish absence or a complete transition interval. */
 if(snapshot->truncated){
  if(!h->gap)wr_roam_event_add(h,now,NULL,WR_ROAM_GAP,0,0);
  h->gap=1;for(i=0;i<h->count;i++)h->clients[i].band=0;
  return 1;
 }
 h->gap=0;h->has_sample=1;h->last_ms=now;
 for(i=0;i<h->count;i++)h->clients[i].seen=0;
 for(i=0;i<snapshot->count;i++){
  const struct wr_device_record *r=&snapshot->records[i];
  struct wr_roam_client *c;unsigned int band=r->radio.band_mask;
  if(!band||!r->mac[0])continue;
  for(j=0;j<h->count;j++)if(!strcmp(h->clients[j].mac,r->mac))break;
  if(j==h->count){
   if(h->count==WR_DEVICE_LIMIT){h->dropped++;continue;}
   c=&h->clients[h->count++];memset(c,0,sizeof(*c));memcpy(c->mac,r->mac,18);
  }else c=&h->clients[j];
  /* Multiple IP records for one MAC are one observation, not confirmations. */
  if(c->seen){
   if(c->seen!=band){
    if(c->band!=3)wr_roam_event_add(h,now,c->mac,WR_ROAM_AMBIGUOUS,c->band,3);
    c->band=3;c->pending=0;c->confirmations=0;c->seen=3;
   }
   continue;
  }
  c->seen=band;
  if(band==3){
   if(c->band!=3)wr_roam_event_add(h,now,c->mac,WR_ROAM_AMBIGUOUS,c->band,3);
   c->band=3;c->pending=0;c->confirmations=0;continue;
  }
  if(!c->band||c->band==3){
   wr_roam_event_add(h,now,c->mac,WR_ROAM_OBSERVED,0,band);
   c->band=band;c->pending=0;c->confirmations=0;
  }else if(c->band==band){c->pending=0;c->confirmations=0;}
  else{
   if(c->pending!=band){c->pending=band;c->confirmations=1;}
   else if(++c->confirmations>=2){
    wr_roam_event_add(h,now,c->mac,WR_ROAM_BAND_CHANGE,c->band,band);
    c->band=band;c->pending=0;c->confirmations=0;
   }
  }
 }
 for(i=0;i<h->count;i++)if(!h->clients[i].seen){
  h->clients[i].band=0;h->clients[i].pending=0;h->clients[i].confirmations=0;
 }
 return 1;
}
#endif
