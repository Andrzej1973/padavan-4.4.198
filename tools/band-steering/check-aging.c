#include "aging.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
struct fixture { unsigned count; int fail_radio; struct wr_band_request sent[2]; };
static int send_request(size_t radio, enum wr_band_protocol protocol,
                        const struct wr_band_request *r, void *ctx)
{
    struct fixture *f = ctx;
    assert(radio < 2 && protocol == (radio ? WR_MT76X2 : WR_MT76X3));
    assert(r->command == WR_IDLE_QUERY && r->cookie);
    f->sent[radio] = *r; f->count++;
    return f->fail_radio == (int)radio ? -1 : 0;
}
static void init(struct wr_band_clients *b, struct wr_band_aging *a, struct fixture *f)
{
    const struct wr_band_radio_config cfg[2] = {{WR_MT76X3, "ra0", 2}, {WR_MT76X2, "rai0", 1}};
    struct wr_band_event e = {0};
    memset(f, 0, sizeof(*f)); f->fail_radio = -1;
    assert(wr_band_clients_init(b, cfg) == 0);
    e.type = WR_EVENT_CLIENT; e.band = 2; e.mac[0] = 2; e.mac[5] = 1;
    assert(wr_band_clients_observe(b, 0, &e, 1) == 0);
    assert(wr_band_aging_init(a, b, 1, send_request, f) == 0);
}
static struct wr_band_event reply(const struct fixture *f, size_t radio, uint8_t state)
{
    struct wr_band_event e = {0};
    e.type = WR_EVENT_IDLE; e.cookie = f->sent[radio].cookie;
    e.table_index = f->sent[radio].table_index; e.idle_state = state;
    memcpy(e.mac, f->sent[radio].mac, 6); return e;
}
int main(void)
{
    struct wr_band_clients b; struct wr_band_aging a; struct fixture f;
    struct wr_band_event e, old, activity;
    unsigned i;
    init(&b, &a, &f);
    assert(wr_band_aging_begin(&a, 0, 60000) == 0 && !f.count);
    assert(wr_band_aging_begin(&a, 0, 60001) == 1 && f.count == 2);
    assert(f.sent[0].cookie != f.sent[1].cookie);
    assert(wr_band_aging_begin(&a, 0, 60002) == 0 && f.count == 2);
    e = reply(&f, 0, 0);
    assert(wr_band_aging_event(&a, 0, &e, 60002) == 1 && b.entries[0].used);
    assert(b.entries[0].record_needs_sync[0]);
    assert(wr_band_aging_event(&a, 0, &e, 60003) == 1 && b.entries[0].used);
    e = reply(&f, 1, 0);
    assert(wr_band_aging_event(&a, 1, &e, 60004) == 2 && !b.entries[0].used);
    /* Reuse the slot for a different MAC; old replies cannot remove or dirty it. */
    activity = (struct wr_band_event){0}; activity.type = WR_EVENT_CLIENT;
    activity.band = 2; activity.mac[0] = 2; activity.mac[5] = 2;
    assert(wr_band_clients_observe(&b, 0, &activity, 60004) == 0);
    assert(wr_band_aging_event(&a, 1, &e, 60005) == 0 && b.entries[0].used);
    assert(!b.entries[0].record_needs_sync[1]);
    /* Same-millisecond activity must invalidate a pending transaction. */
    init(&b, &a, &f);
    assert(wr_band_aging_begin(&a, 0, 60001) == 1);
    e = reply(&f, 0, 0); assert(wr_band_aging_event(&a, 0, &e, 60001) == 1);
    activity.mac[5] = 1;
    assert(wr_band_clients_observe(&b, 0, &activity, 60001) == 0);
    e = reply(&f, 1, 0);
    assert(wr_band_aging_event(&a, 1, &e, 60001) == 0 && b.entries[0].used);
    assert(b.entries[0].record_needs_sync[1]);
    /* Present/error response, from either radio, retains the record. */
    for (i = 0; i < 2; ++i) {
        unsigned state;
        for (state = 1; state <= 2; ++state) {
            init(&b, &a, &f); assert(wr_band_aging_begin(&a, 0, 60001) == 1);
            e = reply(&f, i, (uint8_t)state);
            assert(wr_band_aging_event(&a, i, &e, 60002) == 1);
            e = reply(&f, 1 - i, 0);
            assert(wr_band_aging_event(&a, 1 - i, &e, 60003) == 0 && b.entries[0].used);
        }
    }
    /* Wrong cookie/radio/MAC cannot satisfy a reply. */
    init(&b, &a, &f); assert(wr_band_aging_begin(&a, 0, 60001) == 1);
    e = reply(&f, 0, 0); old = e; e.cookie++;
    assert(wr_band_aging_event(&a, 0, &e, 60002) == 0);
    e = old; assert(wr_band_aging_event(&a, 1, &e, 60002) == 0);
    e.mac[5]++;
    assert(wr_band_aging_event(&a, 0, &e, 60002) == 0);
    /* Timeout never frees. A late removal still invalidates grant assumptions. */
    assert(wr_band_aging_tick(&a, 63001) == 0 && b.entries[0].used);
    e = reply(&f, 0, 0);
    assert(wr_band_aging_event(&a, 0, &e, 63002) == 0 && b.entries[0].used);
    old = e;
    assert(wr_band_aging_begin(&a, 0, 63003) == 1);
    assert(wr_band_aging_event(&a, 0, &old, 63004) == 0 && !a.pending[0].absent_mask);
    assert(wr_band_aging_event(&a, 0, &old, 63003) == -1);
    e = reply(&f, 0, 0); e.cookie = 0;
    assert(wr_band_aging_event(&a, 0, &e, 63005) == -1);
    e.cookie = 1; e.idle_state = 3;
    assert(wr_band_aging_event(&a, 0, &e, 63005) == -1);
    e.idle_state = 0; e.table_index = 64;
    assert(wr_band_aging_event(&a, 0, &e, 63005) == -1);
    assert(wr_band_aging_begin(&a, 64, 64000) == -1);
    /* Either send failure retains the client, including partial submission. */
    for (i = 0; i < 2; ++i) {
        init(&b, &a, &f); f.fail_radio = (int)i;
        assert(wr_band_aging_begin(&a, 0, 60001) == -1 && b.entries[0].used);
        e = reply(&f, 0, 0);
        assert(wr_band_aging_event(&a, 0, &e, 60002) == 0 && b.entries[0].used);
    }
    init(&b, &a, &f); a.next_cookie = UINT32_MAX;
    assert(wr_band_aging_begin(&a, 0, 60001) == -1 && !f.count);
    a.next_cookie = UINT32_MAX - 1;
    assert(wr_band_aging_begin(&a, 0, 60001) == 1 && a.next_cookie == 0);
    assert(wr_band_aging_tick(&a, 63001) == 0);
    assert(wr_band_aging_begin(&a, 0, 63002) == -1);
    assert(wr_band_aging_begin(&a, 0, UINT64_MAX) == -1);
    /* Activity counter saturation fails closed. */
    init(&b, &a, &f); b.entries[0].activity = UINT64_MAX;
    assert(wr_band_clients_observe(&b, 0, &activity, 2) == -1);
    puts("PASS: dual-radio idle proofs, activity generations, slot reuse, stale/duplicate replies, timeout and send failure, cookie exhaustion; no deauth commands");
    return 0;
}
