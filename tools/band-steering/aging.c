#include "aging.h"
#include <string.h>
static int time_ok(struct wr_band_aging *a, uint64_t now)
{
    return a && a->book && now >= a->last_time && now >= a->book->last_time;
}
int wr_band_aging_init(struct wr_band_aging *a, struct wr_band_clients *book,
                       uint64_t now, wr_band_send_callback send, void *ctx)
{
    if (!a || !book || !send || now < book->last_time) return -1;
    memset(a, 0, sizeof(*a)); a->book = book; a->send = send;
    a->context = ctx; a->last_time = now; a->next_cookie = 1;
    return 0;
}
int wr_band_aging_tick(struct wr_band_aging *a, uint64_t now)
{
    size_t i;
    if (!time_ok(a, now)) return -1;
    a->last_time = now; a->book->last_time = now;
    for (i = 0; i < WR_BAND_CLIENT_LIMIT; ++i)
        if (a->pending[i].active && now >= a->pending[i].deadline)
            a->pending[i].active = 0;
    return 0;
}
int wr_band_aging_begin(struct wr_band_aging *a, size_t slot, uint64_t now)
{
    struct wr_band_client *c;
    struct wr_band_pending_idle *p;
    struct wr_band_request r;
    uint64_t last;
    size_t i;
    if (!time_ok(a, now) || slot >= WR_BAND_CLIENT_LIMIT ||
        now > UINT64_MAX - WR_AGING_REPLY_MS) return -1;
    c = &a->book->entries[slot]; p = &a->pending[slot];
    if (!c->used) return -1;
    last = c->last_seen[0] > c->last_seen[1] ? c->last_seen[0] : c->last_seen[1];
    if (now < last) return -1;
    if (p->active && now >= p->deadline) p->active = 0;
    if (p->active || now - last < WR_AGING_IDLE_MS) return 0;
    /* Reserve both cookies before sending, without wrapping or reusing. */
    if (!a->next_cookie || a->next_cookie > UINT32_MAX - 1) return -1;
    memset(p, 0, sizeof(*p)); p->active = 1;
    memcpy(p->mac, c->mac, 6); p->activity = c->activity;
    p->cookie[0] = a->next_cookie++; p->cookie[1] = a->next_cookie++;
    p->deadline = now + WR_AGING_REPLY_MS; a->last_time = now; a->book->last_time = now;
    for (i = 0; i < 2; ++i) {
        memset(&r, 0, sizeof(r)); r.command = WR_IDLE_QUERY;
        r.interface_name = a->book->radios[i].name;
        r.table_index = (uint8_t)slot; r.cookie = p->cookie[i];
        memcpy(r.mac, c->mac, 6);
        if (a->send(i, a->book->radios[i].protocol, &r, a->context) != 0) {
            p->active = 0; return -1;
        }
    }
    return 1;
}
int wr_band_aging_event(struct wr_band_aging *a, size_t radio,
                        const struct wr_band_event *e, uint64_t now)
{
    struct wr_band_pending_idle *p;
    struct wr_band_client *c;
    size_t i;
    if (!time_ok(a, now) || !e || radio >= 2) return -1;
    if (e->type != WR_EVENT_IDLE) return 0;
    if (e->table_index >= WR_BAND_CLIENT_LIMIT || !e->cookie || e->idle_state > 2)
        return -1;
    a->last_time = now; a->book->last_time = now;
    /* Stale replies can still report a real removal. Find by MAC, not just
     * recycled slot, and invalidate policy assumptions conservatively. */
    if (e->idle_state == 0)
        for (i = 0; i < WR_BAND_CLIENT_LIMIT; ++i)
            if (a->book->entries[i].used && !memcmp(a->book->entries[i].mac, e->mac, 6))
                a->book->entries[i].record_needs_sync[radio] = 1;
    p = &a->pending[e->table_index]; c = &a->book->entries[e->table_index];
    if (!p->active || !c->used || p->cookie[radio] != e->cookie ||
        memcmp(p->mac, e->mac, 6) || memcmp(c->mac, e->mac, 6)) return 0;
    if (now >= p->deadline || c->activity != p->activity) {
        p->active = 0; return 0;
    }
    if (e->idle_state != 0) { p->active = 0; return 1; }
    p->absent_mask |= (uint8_t)(1u << radio);
    if (p->absent_mask != 3) return 1;
    memset(c, 0, sizeof(*c)); p->active = 0;
    return 2;
}
