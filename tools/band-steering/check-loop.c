#include "loop.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
struct queued { size_t radio; struct wr_band_request request; };
struct fixture {
    uint64_t now, stop_at;
    unsigned clock_cost, count, cursor, receives, max_receives, waits, disables[2];
    int flood, loss, drop_off, clock_failure, backward, wait_eintr, wait_error;
    struct queued queue[1024];
};
static const struct wr_band_radio_config cfg[2] = {{WR_MT76X3, "ra0", 2}, {WR_MT76X2, "rai0", 1}};
static int send_request(size_t radio, enum wr_band_protocol protocol,
                        const struct wr_band_request *r, void *ctx)
{
    struct fixture *f = ctx;
    assert(radio < 2 && protocol == cfg[radio].protocol && f->count < 1024);
    assert(r->command != WR_DELETE);
    f->queue[f->count].radio = radio; f->queue[f->count++].request = *r;
    if (r->command == WR_ENABLE && !r->enabled) f->disables[radio]++;
    return 0;
}
static int clock_value(void *ctx, uint64_t *out)
{
    struct fixture *f = ctx;
    if (f->clock_failure && f->now >= 400) { errno = EIO; return -1; }
    if (f->backward && f->now >= 400) { *out = 1; return 0; }
    f->now += f->clock_cost; *out = f->now; return 0;
}
static int receive_event(void *ctx, wr_band_event_callback emit, void *owner)
{
    struct fixture *f = ctx;
    f->receives++;
    if (f->loss && f->now >= 400) { errno = ENOBUFS; return -1; }
    while (f->cursor < f->count) {
        struct queued q = f->queue[f->cursor++]; struct wr_band_event e = {0};
        e.band = cfg[q.radio].band;
        if (!q.radio) strcpy(e.interface_name, "ra0");
        if (q.request.command == WR_QUERY) {
            e.type = WR_EVENT_READY; e.ready = 1; e.action = q.radio ? 8 : 9;
            e.channel = q.radio ? 36 : 6;
        } else if (q.request.command == WR_ENABLE) {
            if (!q.request.enabled && f->drop_off) continue;
            e.type = WR_EVENT_ENABLED; e.enabled = q.request.enabled;
        } else continue;
        emit(q.radio, &e, owner); return 1;
    }
    if (f->flood) return 0; /* Valid unrelated datagrams can be endless too. */
    errno = EAGAIN; return -1;
}
static int wait_event(void *ctx, int milliseconds)
{
    struct fixture *f = ctx;
    assert(milliseconds == 100 && f->receives <= 32);
    if (f->receives > f->max_receives) f->max_receives = f->receives;
    f->receives = 0; f->waits++; f->now += (unsigned)milliseconds;
    assert(f->waits < 100);
    if (f->wait_error && f->now >= 400) { errno = EIO; return -1; }
    if (f->wait_eintr && f->now >= 400) { f->wait_eintr = 0; errno = EINTR; return -1; }
    return 0;
}
static int stopping(void *ctx)
{
    struct fixture *f = ctx; return f->now >= f->stop_at;
}
static void init(struct wr_band_coordinator *c, struct fixture *f)
{
    const struct wr_band_policy_config policy = {-70, 1500, 3000, 10000, 30000};
    memset(f, 0, sizeof(*f)); f->stop_at = 1000;
    assert(wr_band_coordinator_init(c, cfg, &policy, 0, send_request, f) == 0);
}
int main(void)
{
    struct wr_band_coordinator c; struct fixture f;
    const struct wr_band_loop_io io = {clock_value, receive_event, wait_event, stopping};
    init(&c, &f);
    assert(wr_band_loop_run(&c, &io, &f) == 0 && c.session.phase == WR_STOPPED);
    assert(f.disables[0] == 1 && f.disables[1] == 1);
    init(&c, &f); f.stop_at = 0;
    assert(wr_band_loop_run(&c, &io, &f) == 0 && !f.count);
    init(&c, &f); f.flood = 1;
    assert(wr_band_loop_run(&c, &io, &f) == 0 && f.max_receives == 32);
    init(&c, &f); f.flood = 1; f.clock_cost = 10;
    assert(wr_band_loop_run(&c, &io, &f) == 0 && f.max_receives <= 5);
    init(&c, &f); f.wait_eintr = 1;
    assert(wr_band_loop_run(&c, &io, &f) == 0 && c.session.phase == WR_STOPPED);
    init(&c, &f); f.loss = 1;
    assert(wr_band_loop_run(&c, &io, &f) == -1 && c.session.phase == WR_FAILED);
    assert(f.disables[0] == 1 && f.disables[1] == 1);
    init(&c, &f); f.clock_failure = 1;
    assert(wr_band_loop_run(&c, &io, &f) == -1 && c.session.phase == WR_FAILED);
    init(&c, &f); f.backward = 1;
    assert(wr_band_loop_run(&c, &io, &f) == -1 && c.session.phase == WR_FAILED);
    init(&c, &f); f.wait_error = 1;
    assert(wr_band_loop_run(&c, &io, &f) == -1 && c.session.phase == WR_FAILED);
    init(&c, &f); f.drop_off = 1;
    assert(wr_band_loop_run(&c, &io, &f) == -1 && c.session.phase == WR_FAILED);
    assert(f.now >= 4000); /* Missing OFF acknowledgement times out, never reports stopped. */
    assert(wr_band_loop_run(&c, NULL, &f) == -1 && errno == EINVAL);
    puts("PASS: persistent event loop, ACK-based signal stop, receive/time budgets, EINTR, event loss, clock/wait faults and missing OFF ACK; all I/O mocked");
    return 0;
}
