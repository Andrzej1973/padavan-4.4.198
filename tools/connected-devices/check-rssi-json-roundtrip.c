#include <assert.h>
#include <stdio.h>
#include "rssi-json.h"
int main(void)
{
 struct wr_rssi_collector c;
 struct wr_rssi_query_response r={0};
 char json[100000];size_t length;unsigned int i;
 wr_rssi_collector_init(&c);
 assert(wr_rssi_json(&c,json,sizeof json,&length));puts(json);
 r.overwritten=~0ULL;r.count=1;r.session[0]=~0ULL;r.session[1]=~0ULL;
 r.records[0].mac[0]=2;r.records[0].attempt=~0U;
 r.records[0].uptime_ms=~0ULL;
 for(i=0;i<256;i++) {
  r.sequence=i+1;r.records[0].sequence=i+1;r.records[0].stage=1+i%4;
  assert(wr_rssi_history_accept(&c.history,0,&r));
 }
 c.history.evicted=~0ULL;c.history.radios[0].missing=~0ULL;
 assert(wr_rssi_json(&c,json,sizeof json,&length));puts(json);
 c.health[0].available=c.health[1].available=1;
 c.health[0].attempted=c.health[1].attempted=1;
 assert(wr_rssi_json(&c,json,sizeof json,&length));puts(json);
 return 0;
}
