#define _GNU_SOURCE
#include "roaming-history.h"
#include <assert.h>
static struct wr_roam_history history;
static struct wr_device_snapshot snapshot;
int main(void){unsigned int before,i;
 snapshot.count=1;strcpy(snapshot.records[0].mac,"02:00:00:00:00:01");
 snapshot.records[0].radio.band_mask=1;
 assert(wr_roam_observe(&history,&snapshot,0,1));assert(history.event_count==1);
 assert(wr_roam_observe(&history,&snapshot,5000,1));assert(history.event_count==1);
 snapshot.records[0].radio.band_mask=2;
 assert(wr_roam_observe(&history,&snapshot,10000,1));assert(history.event_count==1);
 assert(wr_roam_observe(&history,&snapshot,15000,1));
 assert(history.events[1].kind==WR_ROAM_BAND_CHANGE&&history.events[1].before==1&&history.events[1].after==2);
 before=history.event_count;
 assert(wr_roam_observe(&history,NULL,20000,0));
 snapshot.records[0].radio.band_mask=1;
 assert(wr_roam_observe(&history,&snapshot,25000,1));
 assert(history.event_count==before+2&&history.events[before+1].kind==WR_ROAM_OBSERVED);
 snapshot.records[0].radio.band_mask=3;
 assert(wr_roam_observe(&history,&snapshot,30000,1));
 assert(history.events[history.next-1].kind==WR_ROAM_AMBIGUOUS);
 {
  static struct wr_roam_history duplicates;
  static struct wr_device_snapshot input;
  input.count=1;strcpy(input.records[0].mac,"02:00:00:00:00:02");input.records[0].radio.band_mask=1;
  assert(wr_roam_observe(&duplicates,&input,0,1));
  input.records[0].radio.band_mask=2;
  assert(wr_roam_observe(&duplicates,&input,5000,1));
  assert(wr_roam_observe(&duplicates,&input,5000,1));assert(duplicates.event_count==1);
  input.count=2;input.records[1]=input.records[0];input.records[1].radio.band_mask=1;
  assert(wr_roam_observe(&duplicates,&input,10000,1));
  assert(duplicates.event_count==2 && duplicates.events[1].kind==WR_ROAM_AMBIGUOUS);
 }
 snapshot.truncated=1;assert(wr_roam_observe(&history,&snapshot,35000,1));
 assert(history.gap);
 snapshot.truncated=0;
 for(i=0;i<300;i++){assert(wr_roam_observe(&history,NULL,40000+i*10000,0));assert(wr_roam_observe(&history,&snapshot,45000+i*10000,1));}
 assert(history.event_count==256&&history.dropped>0);
 {
  static struct wr_roam_history capacity;
  static struct wr_device_snapshot input;
  input.count=128;
  for(i=0;i<128;i++){
   snprintf(input.records[i].mac,sizeof(input.records[i].mac),"02:00:00:00:00:%02X",i);
   input.records[i].radio.band_mask=1;
  }
  assert(wr_roam_observe(&capacity,&input,0,1));assert(capacity.count==128);
  input.count=0;assert(wr_roam_observe(&capacity,&input,5000,1));
  input.count=1;strcpy(input.records[0].mac,"02:00:00:00:01:00");input.records[0].radio.band_mask=2;
  assert(wr_roam_observe(&capacity,&input,10000,1));
  assert(capacity.count==128 && capacity.client_evictions==1 && capacity.client_dropped==0);
 }
 puts("PASS bounded RAM history, confirmed band observations, gaps/ambiguity and ring overflow; scheduling/actions/runtime pending");
 return 0;
}
