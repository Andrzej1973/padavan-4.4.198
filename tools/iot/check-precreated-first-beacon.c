#include "precreated-first-beacon.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void)
{
 int dev,other;
 struct wr_iot_first_beacon_identity id={&dev,1,2,3,4,5};
 struct wr_iot_first_beacon s={0};
 assert(!wr_iot_first_beacon_arm(NULL,&id));
 assert(wr_iot_first_beacon_arm(&s,&id));
 assert(!wr_iot_first_beacon_arm(&s,&id));
 /* No tick/submission: never ACTIVE merely because raw open returned. */
 assert(!wr_iot_first_beacon_finish(&s,&id,1));
 assert(!wr_iot_first_beacon_arm(&s,&id));
 id.request_generation++;
 assert(wr_iot_first_beacon_arm(&s,&id));
 assert(!wr_iot_first_beacon_submitted(&s,&id,0));
 assert(!wr_iot_first_beacon_submitted(&s,&id,2));
 for(unsigned fault=0;fault<6;fault++){
  struct wr_iot_first_beacon_identity stale=id;
  switch(fault){
   case 0:stale.device=&other;break;
   case 1:stale.netdev_generation++;break;
   case 2:stale.producer_generation++;break;
   case 3:stale.radio_epoch++;break;
   case 4:stale.open_serial++;break;
   case 5:stale.request_generation--;break;
  }
  assert(!wr_iot_first_beacon_submitted(&s,&stale,1));
  assert(!wr_iot_first_beacon_finish(&s,&stale,1));
  assert(!wr_iot_first_beacon_expire(&s,&stale));
  assert(s.pending&&!s.submitted);
 }
 assert(wr_iot_first_beacon_submitted(&s,&id,1));
 assert(!wr_iot_first_beacon_submitted(&s,&id,1));
 assert(!wr_iot_first_beacon_finish(&s,&id,0));
 assert(!wr_iot_first_beacon_finish(&s,&id,1));
 id.request_generation++;
 assert(wr_iot_first_beacon_arm(&s,&id));
 assert(wr_iot_first_beacon_submitted(&s,&id,1));
 assert(wr_iot_first_beacon_finish(&s,&id,1));
 assert(!wr_iot_first_beacon_finish(&s,&id,1));
 id.request_generation++;
 assert(wr_iot_first_beacon_arm(&s,&id));
 assert(wr_iot_first_beacon_expire(&s,&id));
 assert(!wr_iot_first_beacon_submitted(&s,&id,1));
 assert(!wr_iot_first_beacon_finish(&s,&id,1));
 /* Cancellation after accepted enqueue also prevents reporting active. */
 id.request_generation++;
 assert(wr_iot_first_beacon_arm(&s,&id));
 assert(wr_iot_first_beacon_submitted(&s,&id,1));
 assert(wr_iot_first_beacon_expire(&s,&id));
 assert(!wr_iot_first_beacon_finish(&s,&id,1));
 s.last_request=~0ULL;id.request_generation=1;
 assert(!wr_iot_first_beacon_arm(&s,&id));
 memset(&s,0,sizeof(s));id.device=NULL;
 assert(!wr_iot_first_beacon_arm(&s,&id));
 puts("PASS first-beacon host receipt: pending without submission; identity mismatches/replay/late events/cancel/owner loss refuse; one current accepted submission consumed once. No driver hook, RF or TxS proof.");
 return 0;
}
