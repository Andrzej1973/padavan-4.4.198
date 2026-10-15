#include <assert.h>
#include <time.h>
#include "status-runtime.h"
static uint64_t monotonic_now(void)
{
    struct timespec now;
    assert(clock_gettime(CLOCK_MONOTONIC, &now) == 0);
    return (uint64_t)now.tv_sec;
}
int main(void)
{
    struct wr_eoip_status_runtime r;
    unsigned i;
    wr_eoip_status_init(&r);
    assert(r.fd == -1 && !r.pid && !r.valid);
    assert(wr_eoip_status_start(&r, monotonic_now()));
    assert(!wr_eoip_status_start(&r, monotonic_now()));
    for (i = 0; i < 200 && r.pid > 0; i++) {
        wr_eoip_status_tick(&r, monotonic_now());
        usleep(10000);
    }
    assert(!r.pid && r.fd == -1 && r.valid);
    for (i = 0; i < 8; i++) assert(r.cached.present[i] >= 0 && r.cached.present[i] <= 2);
    assert(wr_eoip_status_start(&r, monotonic_now()));
    wr_eoip_status_cancel(&r);
    for (i = 0; i < 200 && r.pid > 0; i++) {
        wr_eoip_status_tick(&r, monotonic_now());
        usleep(10000);
    }
    assert(!r.pid && r.fd == -1 && !r.valid);
    puts("PASS EoIP background status: read-only queries, single child, nonblocking reap and cancellation");
    return 0;
}
