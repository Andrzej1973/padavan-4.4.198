#ifndef WR_RSSI_COLLECTOR_H
#define WR_RSSI_COLLECTOR_H
#include <errno.h>
#include "rssi-history.h"
#include "rssi-query-client.h"
struct wr_rssi_collector_health {
 unsigned long long failures,recoveries,last_success_ms;
 unsigned int available,attempted;
 int error;
};
struct wr_rssi_collector {
 struct wr_rssi_history history;
 struct wr_rssi_collector_health health[2];
};
static inline void wr_rssi_collector_init(struct wr_rssi_collector *c)
{
 if(!c)return;
 *c=(struct wr_rssi_collector){0};wr_rssi_history_init(&c->history);
}
/* One synchronous query per radio per scheduled tick. Interface names come
 * from the internal board mapping, never HTTP input. Failures retain history;
 * ESTALE clears only that radio's cursor for the next tick. */
static inline void wr_rssi_collector_tick(struct wr_rssi_collector *c,
 const char *const interfaces[2],wr_rssi_ioctl_fn invoke,void *context,
 unsigned long long now_ms)
{
 unsigned int radio;
 if(!c||!interfaces||!invoke)return;
 for(radio=0;radio<2;radio++) {
  struct wr_rssi_query_response response;
  struct wr_rssi_collector_health *h=&c->health[radio];
  int result,error;
  errno=0;
  result=wr_rssi_query_client(interfaces[radio],&c->history.radios[radio].cursor,
                            invoke,context,&response);
  error=errno;
  if(result==1&&wr_rssi_history_accept(&c->history,radio,&response)) {
   if(h->attempted&&!h->available)
    h->recoveries=wr_rssi_history_add(h->recoveries,1);
   h->available=1;h->error=0;h->last_success_ms=now_ms;
  } else {
   h->available=0;h->error=result<0?(error?error:EIO):EPROTO;
   h->failures=wr_rssi_history_add(h->failures,1);
   if(result<0&&error==ESTALE)wr_rssi_history_restart(&c->history,radio);
  }
  h->attempted=1;
 }
}
#endif
