#include "session.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
struct fixture { int query[2], enable[2], disable[2], heartbeat[2], fail_enable; };
static const struct wr_band_radio_config radios[2] = {
    {WR_MT76X3, "ra0", 2}, {WR_MT76X2, "rai0", 1}
};
static int send_command(size_t i, enum wr_band_protocol proto,
                        const struct wr_band_request *r, void *context)
{
    struct fixture *f = context;
    uint8_t bytes[80];
    assert(i < 2 && proto == radios[i].protocol);
    assert(wr_band_encode(proto, r, bytes, sizeof(bytes)) > 0);
    if (r->command == WR_QUERY) ++f->query[i];
    else if (r->command == WR_HEARTBEAT) ++f->heartbeat[i];
    else if (r->command == WR_ENABLE) {
        if (r->enabled) { ++f->enable[i]; if (f->fail_enable && i == 1) return -1; }
        else ++f->disable[i];
    }
    return 0;
}
static void ready(struct wr_band_session *s, size_t i, uint64_t now)
{
    struct wr_band_event e = {0};
    e.type = WR_EVENT_READY; e.ready = 1; e.band = radios[i].band;
    e.action = i ? 8 : 9; e.channel = i ? 36 : 6;
    if (!i) strcpy(e.interface_name, "ra0");
    assert(wr_band_session_event(s, i, &e, now) == 0);
}
static void enabled(struct wr_band_session *s, size_t i, int value, uint64_t now)
{
    struct wr_band_event e = {0};
    e.type = WR_EVENT_ENABLED; e.enabled = (uint8_t)value; e.band = radios[i].band;
    if (!i) strcpy(e.interface_name, "ra0");
    assert(wr_band_session_event(s, i, &e, now) == 0);
}
static void start(struct wr_band_session *s, struct fixture *f)
{
    memset(f, 0, sizeof(*f));
    assert(wr_band_session_init(s, radios, 0, send_command, f) == 0);
    assert(wr_band_session_tick(s, 0) == 0 && f->query[0] == 1 && f->query[1] == 1);
    ready(s, 0, 10);
    assert(wr_band_session_tick(s, 20) == 0 && s->phase == WR_QUERYING && !f->enable[0]);
    ready(s, 1, 30);
    assert(wr_band_session_tick(s, 40) == 0 && s->phase == WR_ENABLING);
}
int main(void)
{
    struct wr_band_session s;
    struct fixture f;
    struct wr_band_event e = {0};
    start(&s, &f);
    assert(f.enable[0] == 1 && f.enable[1] == 1 && f.heartbeat[0] == 1 && !f.heartbeat[1]);
    enabled(&s, 0, 1, 50); assert(s.phase == WR_ENABLING);
    enabled(&s, 1, 1, 60); assert(s.phase == WR_ACTIVE);
    assert(wr_band_session_tick(&s, 2040) == 0 && f.heartbeat[0] == 2);
    assert(wr_band_session_stop(&s, 2050) == 0 && s.phase == WR_STOPPING);
    enabled(&s, 0, 0, 2060); assert(s.phase == WR_STOPPING);
    assert(!wr_band_session_off_confirmed(&s));
    enabled(&s, 1, 0, 2070); assert(s.phase == WR_STOPPED);
    assert(wr_band_session_off_confirmed(&s));
    assert(wr_band_session_tick(&s, 9000) == 0);
    start(&s, &f);
    assert(wr_band_session_tick(&s, 5040) == -1 && s.phase == WR_FAILED);
    assert(f.disable[0] == 1 && f.disable[1] == 1);
    start(&s, &f); enabled(&s, 0, 1, 50); enabled(&s, 1, 1, 60);
    e.type = WR_EVENT_REJECTED;
    assert(wr_band_session_event(&s, 0, &e, 70) == -1 && s.phase == WR_FAILED);
    start(&s, &f);
    assert(wr_band_session_stop(&s, 50) == 0);
    assert(wr_band_session_tick(&s, 3050) == -1 && s.phase == WR_FAILED);
    start(&s, &f); enabled(&s, 0, 1, 50); enabled(&s, 1, 1, 60);
    assert(wr_band_session_tick(&s, 10041) == -1 && s.phase == WR_FAILED);
    start(&s, &f); enabled(&s, 0, 1, 50); enabled(&s, 1, 1, 60);
    assert(wr_band_session_tick(&s, 5000) == 0);
    assert(wr_band_session_tick(&s, 10000) == 0);
    assert(wr_band_session_tick(&s, 15040) == -1 && s.phase == WR_FAILED);
    memset(&f, 0, sizeof(f)); f.fail_enable = 1;
    assert(wr_band_session_init(&s, radios, 0, send_command, &f) == 0);
    ready(&s, 0, 10); ready(&s, 1, 20);
    assert(wr_band_session_tick(&s, 30) == -1 && f.disable[0] == 1 && f.disable[1] == 1);
    assert(wr_band_session_init(&s, radios, 0, send_command, &f) == 0);
    assert(wr_band_session_tick(&s, 10000) == -1 && s.phase == WR_FAILED);
    assert(wr_band_session_init(&s, radios, 0, send_command, &f) == 0);
    ready(&s, 0, 10);
    assert(wr_band_session_tick(&s, 9) == -1 && s.phase == WR_FAILED);
    assert(wr_band_session_init(&s, radios, 0, send_command, &f) == 0);
    memset(&e, 0, sizeof(e)); e.type = WR_EVENT_READY; e.ready = 1; e.band = 2;
    strcpy(e.interface_name, "ra1");
    assert(wr_band_session_event(&s, 0, &e, 1) == 0 && !s.ready[0]);
    assert(!wr_band_session_stop(&s, 2) && s.phase == WR_STOPPED);
    assert(!wr_band_session_off_confirmed(&s));
    memset(&f, 0, sizeof(f));
    assert(!wr_band_session_init(&s, radios, 0, send_command, &f));
    assert(!wr_band_session_quiesce(&s, 1) && s.phase == WR_STOPPING);
    assert(f.disable[0] == 1 && f.disable[1] == 1 && !f.enable[0] && !f.enable[1]);
    enabled(&s, 0, 0, 2);
    assert(!wr_band_session_off_confirmed(&s));
    enabled(&s, 1, 0, 3);
    assert(wr_band_session_off_confirmed(&s));
    assert(!wr_band_session_tick(&s, 4) && !f.enable[0] && !f.enable[1]);
    memset(&f, 0, sizeof(f));
    assert(!wr_band_session_init(&s, radios, 0, send_command, &f));
    assert(!wr_band_session_quiesce(&s, 1));
    assert(wr_band_session_tick(&s, 3001) == -1 && !wr_band_session_off_confirmed(&s));
    puts("PASS: two-radio readiness, enable acknowledgements, heartbeat, shutdown and failures; no driver calls");
    return 0;
}
