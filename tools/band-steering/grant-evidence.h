#ifndef WR_BAND_GRANT_EVIDENCE_H
#define WR_BAND_GRANT_EVIDENCE_H
#include "grants.h"
#include <string.h>
/* Called around the actual coordinator callback. Matching pending state is
 * required before dispatch; confirmation is accepted only after dispatch. */
static inline int wr_band_grant_evidence(const struct wr_band_grants *g,size_t radio,
 const struct wr_band_event *e,int after){
 const struct wr_grant_slot *s;const struct wr_grant_radio *r;const struct wr_band_client *c;
 if(!g||!g->book||!e||radio>=2||e->type!=WR_EVENT_GRANT||e->table_index>=WR_BAND_CLIENT_LIMIT||!e->cookie)return 0;
 s=&g->slots[e->table_index];r=&s->radio[radio];c=&g->book->entries[e->table_index];
 if(!s->used||!c->used||s->birth!=c->first_seen||memcmp(s->mac,c->mac,6)||memcmp(s->mac,e->mac,6)||r->cookie!=e->cookie||r->activity!=c->activity)return 0;
 if(!after)return r->phase!=WR_GRANT_NONE&&r->wanted;
 return r->phase==WR_GRANT_NONE&&r->confirmed&&r->verified_at==g->last_time;
}
#endif
