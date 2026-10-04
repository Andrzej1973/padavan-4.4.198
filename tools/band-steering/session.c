#include "session.h"
#include <string.h>
static int command(struct wr_band_session *s, size_t radio, enum wr_band_command code, int enabled)
{
    struct wr_band_request r;
    memset(&r, 0, sizeof(r));
    r.command = code; r.interface_name = s->radios[radio].name;
    r.enabled = (uint8_t)enabled; r.band = s->radios[radio].band;
    r.channel = s->channel[radio]; r.mode = 1; /* PRE_CONNECTION_STEERING */
    return s->send(radio, s->radios[radio].protocol, &r, s->context);
}
void wr_band_session_fault(struct wr_band_session *s)
{
    size_t i;
    if (!s || s->phase == WR_FAILED) return;
    s->phase = WR_FAILED;
    /* Best effort; failure does not establish that the driver is disabled. */
    for (i = 0; i < 2; ++i) if (s->attempted[i]) (void)command(s, i, WR_ENABLE, 0);
}
int wr_band_session_init(struct wr_band_session *s, const struct wr_band_radio_config cfg[2],
                         uint64_t now, wr_band_send_callback send, void *ctx)
{
    struct wr_band_request r;
    uint8_t check[80];
    size_t i;
    if (!s || !cfg || !send || now > UINT64_MAX - 60000) return -1;
    for (i = 0; i < 2; ++i) {
        if (!memchr(cfg[i].name, 0, sizeof(cfg[i].name)) ||
            (cfg[i].band != 1 && cfg[i].band != 2)) return -1;
        memset(&r, 0, sizeof(r)); r.command = WR_QUERY; r.interface_name = cfg[i].name;
        if (wr_band_encode(cfg[i].protocol, &r, check, sizeof(check)) < 0) return -1;
    }
    if (cfg[0].band == cfg[1].band || strcmp(cfg[0].name, cfg[1].name) == 0) return -1;
    memset(s, 0, sizeof(*s)); memcpy(s->radios, cfg, sizeof(s->radios));
    s->send = send; s->context = ctx; s->phase = WR_QUERYING;
    s->last_tick = s->last_time = now; s->deadline = now + 10000; s->next_query = now;
    return 0;
}
int wr_band_session_stop(struct wr_band_session *s, uint64_t now)
{
    size_t i;
    int failed = 0;
    if (!s || now < s->last_time || now > UINT64_MAX - 60000) return -1;
    s->last_time = now;
    if (s->phase == WR_FAILED) return -1;
    if (s->phase == WR_STOPPED || s->phase == WR_STOPPING) return 0;
    s->phase = WR_STOPPING; s->deadline = now + 3000;
    for (i = 0; i < 2; ++i)
        if (s->attempted[i] && command(s, i, WR_ENABLE, 0) < 0) failed = 1;
    if (failed) { s->phase = WR_FAILED; return -1; }
    if (!s->attempted[0] && !s->attempted[1]) s->phase = WR_STOPPED;
    return 0;
}
int wr_band_session_tick(struct wr_band_session *s, uint64_t now)
{
    size_t i;
    if (!s || s->phase == WR_FAILED) return -1;
    if (now < s->last_time || now > UINT64_MAX - 60000) { wr_band_session_fault(s); return -1; }
    if (s->phase == WR_ACTIVE && now - s->last_tick > 10000) { wr_band_session_fault(s); return -1; }
    s->last_tick = s->last_time = now;
    if (s->phase == WR_STOPPED) return 0;
    if ((s->phase == WR_QUERYING || s->phase == WR_ENABLING || s->phase == WR_STOPPING) && now >= s->deadline) {
        wr_band_session_fault(s); return -1;
    }
    if (s->phase == WR_STOPPING) return 0;
    if (s->phase == WR_QUERYING && s->ready[0] && s->ready[1]) {
        s->phase = WR_ENABLING; s->deadline = now + 5000; s->next_heartbeat = now;
        for (i = 0; i < 2; ++i) {
            s->attempted[i] = 1;
            if (command(s, i, WR_ENABLE, 1) < 0) { wr_band_session_fault(s); return -1; }
        }
    }
    if (s->phase == WR_ACTIVE) {
        for (i = 0; i < 2; ++i) if (now - s->last_status[i] > 15000) { wr_band_session_fault(s); return -1; }
    }
    if ((s->phase == WR_QUERYING || s->phase == WR_ACTIVE) && now >= s->next_query) {
        for (i = 0; i < 2; ++i) if (command(s, i, WR_QUERY, 0) < 0) { wr_band_session_fault(s); return -1; }
        s->next_query = now + (s->phase == WR_QUERYING ? 1000 : 5000);
    }
    if ((s->phase == WR_ENABLING || s->phase == WR_ACTIVE) && now >= s->next_heartbeat) {
        for (i = 0; i < 2; ++i) if (s->radios[i].protocol == WR_MT76X3 &&
            command(s, i, WR_HEARTBEAT, 0) < 0) { wr_band_session_fault(s); return -1; }
        s->next_heartbeat = now + 2000;
    }
    return 0;
}
int wr_band_session_event(struct wr_band_session *s, size_t i, const struct wr_band_event *e, uint64_t now)
{
    if (!s || !e || i >= 2 || now < s->last_time || now > UINT64_MAX - 60000 ||
        e->ready > 1 || e->enabled > 1) return -1;
    s->last_time = now;
    if (s->phase == WR_FAILED || s->phase == WR_STOPPED) return 0;
    if (s->radios[i].protocol == WR_MT76X3 && e->interface_name[0] &&
        strncmp(e->interface_name, s->radios[i].name, 16) != 0) return 0;
    if (s->radios[i].protocol == WR_MT76X3 && e->type == WR_EVENT_ENABLED &&
        !(e->band & s->radios[i].band)) return 0;
    if (e->type == WR_EVENT_REJECTED) { wr_band_session_fault(s); return -1; }
    if (e->type == WR_EVENT_READY) {
        if (s->radios[i].protocol == WR_MT76X2 &&
            e->action != (s->radios[i].band == 2 ? 7 : 8)) return 0;
        if (s->radios[i].protocol == WR_MT76X3 && !(e->band & s->radios[i].band)) return 0;
        s->ready[i] = e->ready; s->channel[i] = e->channel; s->last_status[i] = now;
        if (!e->ready && (s->phase == WR_ENABLING || s->phase == WR_ACTIVE)) { wr_band_session_fault(s); return -1; }
    }
    if (e->type == WR_EVENT_ENABLED) {
        if (s->phase == WR_STOPPING && !e->enabled) {
            s->attempted[i] = 0; s->enabled[i] = 0;
            if (!s->attempted[0] && !s->attempted[1]) s->phase = WR_STOPPED;
        } else if (s->phase == WR_ENABLING) {
            if (!e->enabled) { wr_band_session_fault(s); return -1; }
            s->enabled[i] = 1;
            if (s->enabled[0] && s->enabled[1]) { s->phase = WR_ACTIVE; s->next_query = now; }
        } else if (s->phase == WR_ACTIVE && !e->enabled) { wr_band_session_fault(s); return -1; }
    }
    return 0;
}
