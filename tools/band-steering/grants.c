#include "grants.h"
#include <string.h>
#define REPLY_MS 3000
#define REFRESH_MS 5000
static int time_ok(struct wr_band_grants *g, uint64_t now)
{
    return g && g->book && !g->failed && now >= g->last_time &&
           now >= g->book->last_time && now <= UINT64_MAX - REPLY_MS;
}
static int fail(struct wr_band_grants *g) { g->failed = 1; return -1; }
static int matches(const struct wr_grant_slot *s, const struct wr_band_client *c)
{
    return s->used && c->used && s->birth == c->first_seen && !memcmp(s->mac, c->mac, 6);
}
static struct wr_grant_slot *adopt(struct wr_band_grants *g, size_t slot)
{
    struct wr_grant_slot *s = &g->slots[slot];
    const struct wr_band_client *c = &g->book->entries[slot];
    if (!matches(s, c)) {
        memset(s, 0, sizeof(*s)); s->used = 1; s->birth = c->first_seen;
        memcpy(s->mac, c->mac, 6);
    }
    return s;
}
static int send_command(struct wr_band_grants *g, size_t slot, size_t radio,
                         enum wr_band_command command, uint32_t cookie)
{
    struct wr_band_request r = {0};
    r.command = command; r.interface_name = g->book->radios[radio].name;
    r.table_index = (uint8_t)slot; r.cookie = cookie;
    memcpy(r.mac, g->slots[slot].mac, 6);
    if (g->send(radio, g->book->radios[radio].protocol, &r, g->context)) return fail(g);
    return 0;
}
static int query(struct wr_band_grants *g, size_t slot, size_t radio,
                  enum wr_grant_phase phase, uint64_t now)
{
    struct wr_grant_radio *r = &g->slots[slot].radio[radio];
    if (!g->next_cookie) return fail(g);
    r->cookie = g->next_cookie++;
    r->activity = g->book->entries[slot].activity;
    r->deadline = now + REPLY_MS; r->phase = phase;
    return send_command(g, slot, radio, WR_GRANT_QUERY, r->cookie);
}
int wr_band_grants_init(struct wr_band_grants *g, struct wr_band_clients *b,
                        uint64_t now, wr_band_send_callback send, void *ctx)
{
    if (!g || !b || !send || now < b->last_time || now > UINT64_MAX - REPLY_MS) return -1;
    memset(g, 0, sizeof(*g)); g->book = b; g->send = send;
    g->context = ctx; g->last_time = now; g->next_cookie = 1; return 0;
}
int wr_band_grants_tick(struct wr_band_grants *g, uint64_t now)
{
    size_t i, radio;
    if (!time_ok(g, now)) return -1;
    g->last_time = now; g->book->last_time = now;
    for (i = 0; i < WR_BAND_CLIENT_LIMIT; ++i)
        for (radio = 0; radio < 2; ++radio)
            if (matches(&g->slots[i], &g->book->entries[i]) &&
                g->slots[i].radio[radio].phase != WR_GRANT_NONE &&
                now >= g->slots[i].radio[radio].deadline) return fail(g);
    return 0;
}
int wr_band_grants_sync(struct wr_band_grants *g, size_t slot, uint8_t desired, uint64_t now)
{
    struct wr_grant_slot *s;
    size_t radio;
    if (!time_ok(g, now) || slot >= WR_BAND_CLIENT_LIMIT || (desired & ~3u) ||
        !g->book->entries[slot].used) return -1;
    if (wr_band_grants_tick(g, now)) return -1;
    s = adopt(g, slot);
    for (radio = 0; radio < 2; ++radio) {
        struct wr_grant_radio *r = &s->radio[radio];
        r->wanted = (uint8_t)((desired >> radio) & 1u);
        if (!r->wanted) { r->phase = WR_GRANT_NONE; continue; }
        if (r->phase != WR_GRANT_NONE) continue;
        if (!r->confirmed || g->book->entries[slot].record_needs_sync[radio] ||
            now - r->verified_at >= REFRESH_MS)
            if (query(g, slot, radio, WR_GRANT_QUERYING, now)) return -1;
    }
    return 0;
}
int wr_band_grants_invalidate(struct wr_band_grants *g, size_t slot, size_t radio, uint64_t now)
{
    struct wr_grant_radio *r;
    if (!time_ok(g, now) || slot >= WR_BAND_CLIENT_LIMIT || radio >= 2 ||
        !g->book->entries[slot].used) return -1;
    r = &adopt(g, slot)->radio[radio];
    memset(r, 0, sizeof(*r)); g->book->entries[slot].record_needs_sync[radio] = 1;
    g->last_time = now; g->book->last_time = now; return 0;
}
uint8_t wr_band_grants_confirmed(const struct wr_band_grants *g, size_t slot)
{
    size_t i; uint8_t mask = 0;
    if (!g || !g->book || g->failed || slot >= WR_BAND_CLIENT_LIMIT ||
        !matches(&g->slots[slot], &g->book->entries[slot])) return 0;
    for (i = 0; i < 2; ++i)
        if (g->slots[slot].radio[i].confirmed && !g->book->entries[slot].record_needs_sync[i])
            mask |= (uint8_t)(1u << i);
    return mask;
}
int wr_band_grants_event(struct wr_band_grants *g, size_t radio,
                         const struct wr_band_event *e, uint64_t now)
{
    struct wr_grant_slot *s; struct wr_grant_radio *r;
    struct wr_band_client *c;
    if (!time_ok(g, now) || !e || radio >= 2) return -1;
    if (e->type != WR_EVENT_GRANT) return 0;
    if (e->table_index >= WR_BAND_CLIENT_LIMIT || !e->cookie || e->grant_state > 2) return -1;
    g->last_time = now; g->book->last_time = now;
    s = &g->slots[e->table_index]; c = &g->book->entries[e->table_index];
    r = &s->radio[radio];
    if (!matches(s, c) || memcmp(s->mac, e->mac, 6) ||
        r->phase == WR_GRANT_NONE || !r->wanted || r->cookie != e->cookie) return 0;
    if (now >= r->deadline) return fail(g);
    if (r->activity != c->activity) {
        r->phase = WR_GRANT_NONE; r->confirmed = 0; return 0;
    }
    if (e->grant_state == 2) return fail(g);
    if (e->grant_state == 1) {
        r->confirmed = 1; r->verified_at = now; r->phase = WR_GRANT_NONE;
        c->record_needs_sync[radio] = 0; return 1;
    }
    r->confirmed = 0;
    if (r->phase == WR_GRANT_AFTER_ADD) return fail(g);
    if (!g->next_cookie) return fail(g);
    /* Absence established first: do not reset an existing modern entry. */
    if (send_command(g, e->table_index, radio, WR_ADD, 0)) return -1;
    if (query(g, e->table_index, radio, WR_GRANT_AFTER_ADD, now)) return -1;
    return 1;
}
