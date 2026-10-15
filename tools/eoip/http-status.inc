#if defined(BOARD_WR1200JS) && defined(APP_EOIP)
#include "wr-eoip/status-runtime.h"
static struct wr_eoip_status_runtime wr_eoip_http_runtime;
static int wr_eoip_http_initialized;
static void wr_eoip_http_init(void)
{
    if (!wr_eoip_http_initialized) {
        wr_eoip_status_init(&wr_eoip_http_runtime);
        wr_eoip_http_initialized = 1;
    }
}
void wr_eoip_background_tick(void)
{
    if (wr_eoip_http_initialized)
        wr_eoip_status_tick(&wr_eoip_http_runtime, (uint64_t)uptime());
}
void wr_eoip_background_close(void)
{
    if (!wr_eoip_http_initialized) return;
    wr_eoip_status_cancel(&wr_eoip_http_runtime);
    wr_eoip_background_tick();
    /* On HTTP shutdown, init inherits any killed child not yet reapable. */
}
static int ej_wr_eoip_status(int eid, webs_t wp, int argc, char **argv)
{
    uint64_t now = (uint64_t)uptime();
    struct wr_eoip_status_runtime *r = &wr_eoip_http_runtime;
    unsigned slot;
    int written;
    (void)eid; (void)argv;
    if (argc) return websWrite(wp, "{\"error\":\"invalid_request\"}");
    wr_eoip_http_init(); wr_eoip_background_tick();
    if (!r->pid && (!r->valid || now < r->sampled || now - r->sampled >= 10)) {
        if (!wr_eoip_status_start(r, now)) r->valid = 0;
    }
    if (!r->valid || now < r->sampled || now - r->sampled > 60)
        return websWrite(wp, "{\"error\":\"source_unavailable\",\"pending\":%s}", r->pid > 0 ? "true" : "false");
    written = websWrite(wp, "{\"schema\":1,\"sample_age\":%llu,\"pending\":%s,\"slots\":[",
        (unsigned long long)(now - r->sampled), r->pid > 0 ? "true" : "false");
    for (slot = 0; slot < 8; slot++) {
        int present = r->cached.present[slot];
        const struct wr_eoip_observation *o = &r->cached.slots[slot];
        const char *state = present == 1 ? "absent" : present != 2 ? "unknown" :
            !o->owned ? "foreign" : (o->flags & 1U) ? "up" : "down";
        written += websWrite(wp, "%s{\"slot\":%u,\"state\":\"%s\"", slot ? "," : "", slot, state);
        if (present == 2 && o->owned)
            written += websWrite(wp, ",\"ifindex\":%d,\"mtu\":%u,\"master\":%u", o->ifindex, o->mtu, o->master);
        written += websWrite(wp, "}");
    }
    return written + websWrite(wp, "]}");
}
#endif
