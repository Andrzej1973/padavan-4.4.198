#ifndef WR_RSSI_HISTORY_H
#define WR_RSSI_HISTORY_H
#include "rssi-query-cursor.h"
#define WR_RSSI_HISTORY_CAPACITY 256
struct wr_rssi_history_event {
 unsigned long long session[2];
 struct wr_rssi_record record;
};
struct wr_rssi_history_radio {
 struct wr_rssi_query_request cursor;
 unsigned long long missing,restarts,driver_overwritten,last_session[2],last_after;
};
struct wr_rssi_history {
 struct wr_rssi_history_radio radios[2];
 struct wr_rssi_history_event events[WR_RSSI_HISTORY_CAPACITY];
 unsigned int next,count;
 unsigned long long evicted;
};
static inline unsigned long long wr_rssi_history_add(unsigned long long a,
 unsigned long long b)
{ return ~0ULL-a<b?~0ULL:a+b; }
static inline void wr_rssi_history_init(struct wr_rssi_history *h)
{
 unsigned int i;
 if(!h)return;
 *h=(struct wr_rssi_history){0};
 for(i=0;i<2;i++){h->radios[i].cursor.capacity=64;h->radios[i].cursor.radio=i;}
}
/* Called only for ESTALE: retain historical identities and request a new
 * session on the next scheduled tick. No immediate retry loop. */
static inline void wr_rssi_history_restart(struct wr_rssi_history *h,unsigned int radio)
{
 struct wr_rssi_history_radio *s;
 if(!h||radio>1)return;
 s=&h->radios[radio];s->cursor.after=0;
 s->cursor.session[0]=s->cursor.session[1]=0;
 s->restarts=wr_rssi_history_add(s->restarts,1);
}
/* Validate the complete page before mutating history or its cursor. Keep the
 * full 128-bit adapter session on every event; gaps count absent sequences,
 * while ring eviction is a separate counter. */
static inline int wr_rssi_history_accept(struct wr_rssi_history *h,
 unsigned int radio,const struct wr_rssi_query_response *r)
{
 struct wr_rssi_query_request next;
 unsigned long long previous,retained=0,missing=0;
 unsigned int i;unsigned char scratch[32];
 struct wr_rssi_history_radio *s;
 if(!h||!r||radio>1)return 0;
 s=&h->radios[radio];
 if(!wr_rssi_query_next_cursor(&s->cursor,r,&next))return 0;
 if(s->last_session[0]==r->session[0]&&s->last_session[1]==r->session[1])retained=s->last_after;
 if(r->sequence<retained)return 0;
 previous=s->cursor.after>retained?s->cursor.after:retained;
 for(i=0;i<r->count;i++) {
  if(r->records[i].radio!=radio||
     !wr_rssi_query_record_encode(scratch,32,&r->records[i]))return 0;
  if(r->records[i].sequence<=retained)continue;
  missing=wr_rssi_history_add(missing,r->records[i].sequence-previous-1);
  previous=r->records[i].sequence;
 }
 for(i=0;i<r->count;i++) {
  struct wr_rssi_history_event *e;
  if(r->records[i].sequence<=retained)continue;
  e=&h->events[h->next];
  e->session[0]=r->session[0];e->session[1]=r->session[1];e->record=r->records[i];
  h->next=(h->next+1)%WR_RSSI_HISTORY_CAPACITY;
  if(h->count<WR_RSSI_HISTORY_CAPACITY)h->count++;
  else h->evicted=wr_rssi_history_add(h->evicted,1);
 }
 if(next.after<retained)next.after=retained;
 s->driver_overwritten=r->overwritten;
 s->last_session[0]=r->session[0];s->last_session[1]=r->session[1];s->last_after=next.after;
 s->missing=wr_rssi_history_add(s->missing,missing);s->cursor=next;return 1;
}
#endif
