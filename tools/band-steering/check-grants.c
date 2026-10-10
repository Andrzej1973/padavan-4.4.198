#include "grants.h"
#include "grant-evidence.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
struct fixture { unsigned count; int fail_on; struct wr_band_request sent[64], latest[2]; };
static int send_request(size_t radio, enum wr_band_protocol protocol,
                        const struct wr_band_request *r, void *ctx)
{
    struct fixture *f = ctx;
    assert(radio < 2 && protocol == (radio ? WR_MT76X2 : WR_MT76X3));
    assert(r->command == WR_GRANT_QUERY || r->command == WR_ADD);
    assert((r->command == WR_GRANT_QUERY && r->cookie) || (r->command == WR_ADD && !r->cookie));
    assert(f->count < 64); f->sent[f->count] = *r; f->latest[radio] = *r;
    f->count++; return f->fail_on == (int)f->count ? -1 : 0;
}
static void init(struct wr_band_clients *b, struct wr_band_grants *g, struct fixture *f)
{
    const struct wr_band_radio_config cfg[2] = {{WR_MT76X3, "ra0", 2}, {WR_MT76X2, "rai0", 1}};
    struct wr_band_event e = {0};
    memset(f, 0, sizeof(*f)); f->fail_on = -1;
    assert(wr_band_clients_init(b, cfg) == 0);
    e.type = WR_EVENT_CLIENT; e.band = 2; e.mac[0] = 2; e.mac[5] = 1;
    assert(wr_band_clients_observe(b, 0, &e, 0) == 0);
    assert(wr_band_grants_init(g, b, 0, send_request, f) == 0);
}
static struct wr_band_event reply(const struct fixture *f, size_t radio, uint8_t state)
{
    struct wr_band_event e = {0};
    assert(f->latest[radio].command == WR_GRANT_QUERY);
    e.type = WR_EVENT_GRANT; e.cookie = f->latest[radio].cookie;
    e.table_index = f->latest[radio].table_index; e.grant_state = state;
    memcpy(e.mac, f->latest[radio].mac, 6); return e;
}
int main(void)
{
    struct wr_band_clients b; struct wr_band_grants g; struct fixture f;
    struct wr_band_event e, old, activity = {0};
    unsigned count;
    init(&b, &g, &f);
    assert(wr_band_grants_sync(&g, 0, 3, 0) == 0 && f.count == 2);
    assert(!wr_band_grants_confirmed(&g, 0));
    assert(wr_band_grants_sync(&g, 0, 3, 1) == 0 && f.count == 2);
    e = reply(&f, 0, 1);
    assert(wr_band_grant_evidence(&g,0,&e,0));assert(!wr_band_grant_evidence(&g,0,&e,1));
    old=e;old.cookie++;assert(!wr_band_grant_evidence(&g,0,&old,0));
    old=e;old.mac[5]++;assert(!wr_band_grant_evidence(&g,0,&old,0));
    b.entries[0].activity++;assert(!wr_band_grant_evidence(&g,0,&e,0));b.entries[0].activity--;
    assert(wr_band_grants_event(&g, 0, &e, 1) == 1 && wr_band_grants_confirmed(&g, 0) == 1);
    assert(wr_band_grant_evidence(&g,0,&e,1));assert(!wr_band_grant_evidence(&g,0,&e,0));
    old=e;old.mac[5]++;assert(!wr_band_grant_evidence(&g,0,&old,1));
    b.entries[0].first_seen++;assert(!wr_band_grant_evidence(&g,0,&e,1));b.entries[0].first_seen--;

    e = reply(&f, 1, 0); old = e;
    assert(wr_band_grants_event(&g, 1, &e, 1) == 1 && f.count == 4);
    assert(f.sent[2].command == WR_ADD && f.sent[3].command == WR_GRANT_QUERY);
    assert(wr_band_grants_confirmed(&g, 0) == 1);
    assert(wr_band_grants_event(&g, 1, &old, 2) == 0 && f.count == 4);
    e = reply(&f, 1, 1);
    assert(wr_band_grants_event(&g, 1, &e, 2) == 1 && wr_band_grants_confirmed(&g, 0) == 3);
    assert(wr_band_grants_sync(&g, 0, 3, 4999) == 0 && f.count == 4);
    assert(wr_band_grants_sync(&g, 0, 3, 5002) == 0 && f.count == 6);
    e = reply(&f, 0, 1); assert(wr_band_grants_event(&g, 0, &e, 5003) == 1);
    e = reply(&f, 1, 1); assert(wr_band_grants_event(&g, 1, &e, 5003) == 1);
    assert(f.count == 6); /* Refresh never adds an already present record. */
    assert(wr_band_grants_invalidate(&g, 0, 0, 5004) == 0 && wr_band_grants_confirmed(&g, 0) == 2);
    assert(wr_band_grants_sync(&g, 0, 3, 5004) == 0 && f.count == 7);
    e = reply(&f, 0, 1); old = e;
    activity.type = WR_EVENT_CLIENT; activity.band = 2; activity.mac[0] = 2; activity.mac[5] = 1;
    assert(wr_band_clients_observe(&b, 0, &activity, 5004) == 0);
    assert(wr_band_grants_event(&g, 0, &e, 5004) == 0 && wr_band_grants_confirmed(&g, 0) == 2);
    assert(b.entries[0].record_needs_sync[0]);
    assert(wr_band_grants_sync(&g, 0, 3, 5005) == 0 && f.count == 8);
    assert(wr_band_grants_event(&g, 0, &old, 5005) == 0);
    e = reply(&f, 0, 1);
    assert(wr_band_grants_event(&g, 0, &e, 5005) == 1 && wr_band_grants_confirmed(&g, 0) == 3);
    assert(!b.entries[0].record_needs_sync[0]);
    /* Dropped desire cancels pending add, but never deletes an existing grant. */
    init(&b, &g, &f); assert(wr_band_grants_sync(&g, 0, 1, 0) == 0);
    e = reply(&f, 0, 0);
    assert(wr_band_grants_sync(&g, 0, 0, 1) == 0);
    assert(wr_band_grants_event(&g, 0, &e, 1) == 0 && f.count == 1);
    /* Post-add absence is a failure, not success from the preceding ioctl. */
    init(&b, &g, &f); assert(wr_band_grants_sync(&g, 0, 1, 0) == 0);
    e = reply(&f, 0, 0); assert(wr_band_grants_event(&g, 0, &e, 1) == 1);
    e = reply(&f, 0, 0);
    assert(wr_band_grants_event(&g, 0, &e, 2) == -1 && g.failed && !wr_band_grants_confirmed(&g, 0));
    assert(wr_band_grants_sync(&g, 0, 1, 3) == -1);
    /* Presence with an index error also fails closed. */
    init(&b, &g, &f); assert(wr_band_grants_sync(&g, 0, 1, 0) == 0);
    e = reply(&f, 0, 2); assert(wr_band_grants_event(&g, 0, &e, 1) == -1 && g.failed);
    /* Timeouts and transport errors are fatal for the owning session. */
    init(&b, &g, &f); assert(wr_band_grants_sync(&g, 0, 1, 0) == 0);
    assert(wr_band_grants_tick(&g, 3000) == -1 && g.failed);
    for (count = 1; count <= 3; ++count) {
        init(&b, &g, &f); f.fail_on = (int)count;
        if (count == 1) assert(wr_band_grants_sync(&g, 0, 1, 0) == -1 && g.failed);
        else {
            assert(wr_band_grants_sync(&g, 0, 1, 0) == 0);
            e = reply(&f, 0, 0);
            assert(wr_band_grants_event(&g, 0, &e, 1) == -1 && g.failed);
        }
    }
    /* Wrong radio/cookie/MAC, recycled slots and invalid data cannot confirm. */
    init(&b, &g, &f); assert(wr_band_grants_sync(&g, 0, 3, 0) == 0);
    e = reply(&f, 0, 1); old = e;
    assert(wr_band_grants_event(&g, 1, &e, 1) == 0);
    e.cookie += 8; assert(wr_band_grants_event(&g, 0, &e, 1) == 0);
    e = old; e.mac[5] = 2; assert(wr_band_grants_event(&g, 0, &e, 1) == 0);
    b.entries[0].mac[5] = 2; b.entries[0].first_seen = 1;
    e = old; assert(wr_band_grants_event(&g, 0, &e, 1) == 0 && !wr_band_grants_confirmed(&g, 0));
    assert(wr_band_grants_sync(&g, 0, 1, 2) == 0);
    e = reply(&f, 0, 1); assert(e.mac[5] == 2);
    e.cookie = 0; assert(wr_band_grants_event(&g, 0, &e, 2) == -1);
    assert(wr_band_grants_sync(&g, 64, 1, 2) == -1);
    assert(wr_band_grants_sync(&g, 0, 4, 2) == -1);
    assert(wr_band_grants_sync(&g, 0, 1, 1) == -1);
    init(&b, &g, &f); g.next_cookie = UINT32_MAX;
    assert(wr_band_grants_sync(&g, 0, 1, 0) == 0 && !g.next_cookie);
    e = reply(&f, 0, 0);
    assert(wr_band_grants_event(&g, 0, &e, 1) == -1 && f.count == 1); /* No unverified add. */
    /* ASSOC state alone never resets an existing modern grant. */
    init(&b, &g, &f); assert(wr_band_grants_sync(&g, 0, 1, 0) == 0);
    e = reply(&f, 0, 3);
    assert(wr_band_grants_event(&g, 0, &e, 0) == 1 && f.count == 1);
    assert(wr_band_grants_confirmed(&g, 0) == 1);
    activity.frame_type = 3;
    assert(wr_band_clients_observe(&b, 0, &activity, 1) == 0);
    assert(wr_band_grants_auth(&g, 0, 0, &activity, 1) == 1);
    assert(wr_band_grants_sync(&g, 0, 1, 1) == 0 && f.count == 2);
    e = reply(&f, 0, 3);
    assert(wr_band_grants_event(&g, 0, &e, 1) == 1 && f.count == 4);
    assert(f.sent[2].command == WR_ADD && f.sent[3].command == WR_GRANT_QUERY);
    e = reply(&f, 0, 1);
    assert(wr_band_grants_event(&g, 0, &e, 2) == 1 && wr_band_grants_confirmed(&g, 0) == 1);
    /* Another auth request when the record is already INIT needs no reset. */
    assert(wr_band_clients_observe(&b, 0, &activity, 3) == 0);
    assert(wr_band_grants_auth(&g, 0, 0, &activity, 3) == 1);
    assert(wr_band_grants_sync(&g, 0, 1, 3) == 0 && f.count == 5);
    e = reply(&f, 0, 1);
    assert(wr_band_grants_event(&g, 0, &e, 3) == 1 && f.count == 5);
    assert(wr_band_grants_auth(&g, 0, 1, &activity, 3) == 0);
    /* A reset whose post-readback still says ASSOC is not verified. */
    assert(wr_band_clients_observe(&b, 0, &activity, 4) == 0);
    assert(wr_band_grants_auth(&g, 0, 0, &activity, 4) == 1);
    assert(wr_band_grants_sync(&g, 0, 1, 4) == 0);
    e = reply(&f, 0, 3); assert(wr_band_grants_event(&g, 0, &e, 4) == 1);
    e = reply(&f, 0, 3); assert(wr_band_grants_event(&g, 0, &e, 5) == -1 && g.failed);
    puts("PASS: correlated grant ordering/dedup, refresh/invalidation, failures, and modern reauth reset only after auth plus ASSOC proof; no deletes");
    return 0;
}
