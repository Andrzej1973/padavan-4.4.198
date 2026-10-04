#include "loop.h"
#include <errno.h>
struct dispatch { struct wr_band_coordinator *coordinator; uint64_t now; int failed; };
static void event(size_t radio, const struct wr_band_event *e, void *ctx)
{
    struct dispatch *d = ctx;
    if (!d->failed && wr_band_coordinator_event(d->coordinator, radio, e, d->now)) d->failed = 1;
}
static int fault(struct wr_band_coordinator *c)
{
    wr_band_coordinator_fault(c); return -1;
}
static int read_clock(const struct wr_band_loop_io *io, void *ctx, uint64_t *now, uint64_t *last)
{
    if (io->clock(ctx, now)) return -1;
    if (*now < *last) { errno = EINVAL; return -1; }
    *last = *now; return 0;
}
static int stop_if_requested(struct wr_band_coordinator *c, const struct wr_band_loop_io *io,
                             void *ctx, uint64_t now)
{
    if (io->stopping(ctx) && c->session.phase != WR_STOPPING && c->session.phase != WR_STOPPED)
        return wr_band_coordinator_stop(c, now);
    return 0;
}
int wr_band_loop_run(struct wr_band_coordinator *c, const struct wr_band_loop_io *io, void *ctx)
{
    uint64_t now, cycle, last_clock;
    unsigned count;
    if (!c || !io || !io->clock || !io->receive || !io->wait || !io->stopping) {
        errno = EINVAL; return -1;
    }
    last_clock = c->last_time;
    for (;;) {
        if (read_clock(io, ctx, &now, &last_clock)) return fault(c);
        if (stop_if_requested(c, io, ctx, now)) return fault(c);
        if (c->session.phase == WR_STOPPED) return 0;
        if (c->session.phase == WR_FAILED) return -1;
        cycle = now;
        for (count = 0; count < 32; ++count) {
            struct dispatch d;
            int result;
            if (read_clock(io, ctx, &now, &last_clock)) return fault(c);
            if (now < cycle) return fault(c);
            if (now - cycle >= 50) break;
            d.coordinator = c; d.now = now; d.failed = 0;
            result = io->receive(ctx, event, &d);
            if (d.failed) return fault(c);
            if (result < 0) {
                if (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR) break;
                return fault(c); /* Includes ENOBUFS, malformed/truncated kernel events. */
            }
        }
        if (read_clock(io, ctx, &now, &last_clock)) return fault(c);
        if (stop_if_requested(c, io, ctx, now) || wr_band_coordinator_tick(c, now)) return fault(c);
        if (c->session.phase == WR_STOPPED) return 0;
        if (io->wait(ctx, 100) < 0 && errno != EINTR) return fault(c);
    }
}
