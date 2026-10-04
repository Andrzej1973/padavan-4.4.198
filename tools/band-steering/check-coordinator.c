#include "coordinator.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
struct queued { size_t radio; struct wr_band_request request; };
struct fixture {
    struct queued queue[2048]; unsigned count, cursor, disables[2];
    uint8_t record[2], idle[2]; int fail_send;
};
static const struct wr_band_radio_config cfg[2] = {{WR_MT76X3, "ra0", 2}, {WR_MT76X2, "rai0", 1}};
static int send_request(size_t radio, enum wr_band_protocol protocol,
                        const struct wr_band_request *r, void *ctx)
{
    struct fixture *f = ctx;
    assert(radio < 2 && protocol == cfg[radio].protocol && f->count < 2048);
    assert(r->command != WR_DELETE);
    f->queue[f->count].radio = radio; f->queue[f->count].request = *r; f->count++;
    if (r->command == WR_ADD) f->record[radio] = 1;
    if (r->command == WR_ENABLE && !r->enabled) f->disables[radio]++;
    return f->fail_send ? -1 : 0;
}
static void drain(struct wr_band_coordinator *c, struct fixture *f, uint64_t now)
{
    /* Replies delivered after send returns, never through reentrant callbacks. */
    while (f->cursor < f->count) {
        struct queued q = f->queue[f->cursor++];
        struct wr_band_event e = {0};
        e.band = cfg[q.radio].band;
        if (!q.radio) strcpy(e.interface_name, "ra0");
        if (q.request.command == WR_QUERY) {
            e.type = WR_EVENT_READY; e.ready = 1; e.action = q.radio ? 8 : 9;
            e.channel = q.radio ? 36 : 6;
        } else if (q.request.command == WR_ENABLE) {
            e.type = WR_EVENT_ENABLED; e.enabled = q.request.enabled;
        } else if (q.request.command == WR_GRANT_QUERY || q.request.command == WR_IDLE_QUERY) {
            e.type = q.request.command == WR_GRANT_QUERY ? WR_EVENT_GRANT : WR_EVENT_IDLE;
            e.cookie = q.request.cookie; e.table_index = q.request.table_index;
            memcpy(e.mac, q.request.mac, 6);
            if (e.type == WR_EVENT_GRANT) e.grant_state = f->record[q.radio];
            else {
                e.idle_state = f->idle[q.radio];
                if (!e.idle_state) f->record[q.radio] = 0;
            }
        } else continue;
        assert(wr_band_coordinator_event(c, q.radio, &e, now) == 0);
    }
}
static void start(struct wr_band_coordinator *c, struct fixture *f)
{
    const struct wr_band_policy_config policy = {-70, 1500, 3000, 10000, 30000};
    memset(f, 0, sizeof(*f));
    assert(wr_band_coordinator_init(c, cfg, &policy, 0, send_request, f) == 0);
    assert(wr_band_coordinator_tick(c, 0) == 0); drain(c, f, 0);
    assert(c->session.phase == WR_QUERYING);
    assert(wr_band_coordinator_tick(c, 1) == 0); drain(c, f, 1);
    assert(c->session.phase == WR_ACTIVE);
    assert(wr_band_coordinator_tick(c, 2) == 0); drain(c, f, 2);
}
static void probe(struct wr_band_coordinator *c, size_t radio, uint8_t id, uint64_t now)
{
    struct wr_band_event e = {0};
    e.type = WR_EVENT_CLIENT; e.band = cfg[radio].band; e.mac[0] = 2; e.mac[5] = id;
    e.frame_type = 0; e.rssi_count = 1; e.rssi[0] = -60;
    assert(wr_band_coordinator_event(c, radio, &e, now) == 0);
}
static void tick_to(struct wr_band_coordinator *c, struct fixture *f, uint64_t begin, uint64_t end)
{
    uint64_t now;
    for (now = begin; now <= end; now += 1000) {
        assert(wr_band_coordinator_tick(c, now) == 0); drain(c, f, now);
    }
}
int main(void)
{
    struct wr_band_coordinator c; struct fixture f;
    struct wr_band_event e = {0};
    unsigned i, before;
    start(&c, &f); probe(&c, 0, 1, 3);
    assert(wr_band_coordinator_tick(&c, 1502) == 0); drain(&c, &f, 1502);
    assert(!wr_band_grants_confirmed(&c.grants, 0));
    assert(wr_band_coordinator_tick(&c, 1503) == 0); drain(&c, &f, 1503);
    assert(wr_band_grants_confirmed(&c.grants, 0) == 1);
    tick_to(&c, &f, 2503, 61503);
    assert(!c.clients.entries[0].used && c.session.phase == WR_ACTIVE);
    assert(!c.grants.slots[0].used && !c.policy.slots[0].used);
    probe(&c, 1, 2, 61504);
    assert(wr_band_coordinator_tick(&c, 61504) == 0); drain(&c, &f, 61504);
    assert(c.clients.entries[0].mac[5] == 2 && wr_band_grants_confirmed(&c.grants, 0) == 2);
    /* Incoming activity invalidates an aging proof; no grants run during it. */
    start(&c, &f); probe(&c, 0, 1, 3);
    tick_to(&c, &f, 1503, 59503);
    assert(wr_band_coordinator_tick(&c, 60503) == 0 && c.aging.pending[0].active);
    before = f.count;
    probe(&c, 0, 1, 60503);
    assert(wr_band_coordinator_tick(&c, 60504) == 0 && f.count == before);
    drain(&c, &f, 60504);
    assert(c.clients.entries[0].used && !c.aging.pending[0].active);
    assert(!wr_band_grants_confirmed(&c.grants, 0));
    assert(wr_band_coordinator_tick(&c, 60505) == 0); drain(&c, &f, 60505);
    assert(wr_band_grants_confirmed(&c.grants, 0) == 1);
    /* Modern auth event routes to proof-based repair; ordinary probe does not. */
    f.record[0] = 3;
    e.type = WR_EVENT_CLIENT; e.band = 2; e.frame_type = 3; e.mac[0] = 2; e.mac[5] = 1;
    assert(wr_band_coordinator_event(&c, 0, &e, 60506) == 0);
    assert(wr_band_coordinator_tick(&c, 60506) == 0); drain(&c, &f, 60506);
    assert(f.record[0] == 1 && wr_band_grants_confirmed(&c.grants, 0) == 1);
    /* Legacy kick invalidates 5G and routes cooldown without deleting anything. */
    probe(&c, 1, 1, 60507);
    assert(wr_band_coordinator_tick(&c, 60507) == 0); drain(&c, &f, 60507);
    assert(wr_band_grants_confirmed(&c.grants, 0) == 3);
    e.type = WR_EVENT_DELETED; e.band = 0; e.frame_type = 0;
    f.record[1] = 0;
    assert(wr_band_coordinator_event(&c, 1, &e, 60508) == 0);
    assert(wr_band_coordinator_tick(&c, 60508) == 0); drain(&c, &f, 60508);
    assert(wr_band_grants_confirmed(&c.grants, 0) == 1);
    /* Normal stop waits for both radio acknowledgements. */
    assert(wr_band_coordinator_stop(&c, 60509) == 0 && c.session.phase == WR_STOPPING);
    drain(&c, &f, 60509); assert(c.session.phase == WR_STOPPED);
    assert(f.disables[0] == 1 && f.disables[1] == 1);
    /* Capacity exhaustion disables steering rather than blocking untracked MACs. */
    start(&c, &f);
    for (i = 1; i <= 64; ++i) probe(&c, 0, (uint8_t)i, 3);
    e = (struct wr_band_event){0}; e.type = WR_EVENT_CLIENT; e.band = 2; e.mac[0] = 2; e.mac[5] = 65;
    assert(wr_band_coordinator_event(&c, 0, &e, 3) == -1 && c.session.phase == WR_FAILED);
    assert(f.disables[0] == 1 && f.disables[1] == 1);
    start(&c, &f); wr_band_coordinator_fault(&c);
    assert(c.session.phase == WR_FAILED && f.disables[0] == 1 && f.disables[1] == 1);
    start(&c, &f); probe(&c, 0, 1, 3); f.fail_send = 1;
    assert(wr_band_coordinator_tick(&c, 1503) == -1 && c.session.phase == WR_FAILED);
    start(&c, &f); assert(wr_band_coordinator_tick(&c, 1) == -1 && c.session.phase == WR_FAILED);
    puts("PASS: integrated handshake, grant/aging serialization, activity races, slot recycling, modern reauth, legacy kick, acknowledged stop and failure fallback; mocked driver transport");
    return 0;
}
