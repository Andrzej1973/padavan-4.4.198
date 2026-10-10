#ifndef WR_RSSI_QUERY_CURSOR_H
#define WR_RSSI_QUERY_CURSOR_H
#include "rssi-query-decode.h"
/* Response has passed wire validation. Commit only the last returned record,
 * never the driver's latest sequence when a bounded page is incomplete. */
static inline int wr_rssi_query_next_cursor(const struct wr_rssi_query_request *q,
 const struct wr_rssi_query_response *r,struct wr_rssi_query_request *next)
{
 struct wr_rssi_query_request value;unsigned int i;unsigned long long previous;
 if(!q||!r||!next||!q->capacity||q->capacity>64||r->count>q->capacity||
    r->radio!=q->radio||r->sequence<q->after||
    !wr_rssi_query_session_matches(q,r->session))return 0;
 previous=q->after;
 for(i=0;i<r->count;i++) {
  if(r->records[i].sequence<=previous||r->records[i].sequence>r->sequence)return 0;
  previous=r->records[i].sequence;
 }
 if(r->count<q->capacity&&previous!=r->sequence)return 0;
 value=*q;value.after=previous;value.session[0]=r->session[0];value.session[1]=r->session[1];
 *next=value;return 1;
}
#endif
