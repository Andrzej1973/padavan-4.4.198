#include "coordinator.h"
#include <string.h>
void wr_band_coordinator_fault(struct wr_band_coordinator *c)
{
    if (c) wr_band_session_fault(&c->session);
}
static int failure(struct wr_band_coordinator *c)
{
    wr_band_coordinator_fault(c); return -1;
}
static int clock_ok(struct wr_band_coordinator *c, uint64_t now)
{
    return c && now >= c->last_time && now <= UINT64_MAX - 60000;
}
int wr_band_coordinator_init(struct wr_band_coordinator *c, const struct wr_band_radio_config cfg[2],
                             const struct wr_band_policy_config *policy, uint64_t now,
                             wr_band_send_callback send, void *ctx)
{
    if (!c || !cfg || !policy || !send || now > UINT64_MAX - 60000) return -1;
    memset(c, 0, sizeof(*c));
    if (wr_band_clients_init(&c->clients, cfg) || wr_band_policy_init(&c->policy, policy, now) ||
        wr_band_grants_init(&c->grants, &c->clients, now, send, ctx) ||
        wr_band_aging_init(&c->aging, &c->clients, now, send, ctx)) return -1;
    if (wr_band_session_init(&c->session, cfg, now, send, ctx)) return -1;
    c->last_time = now; return 0;
}
int wr_band_coordinator_stop(struct wr_band_coordinator *c, uint64_t now)
{
    if (!clock_ok(c, now)) return c ? failure(c) : -1;
    c->last_time = now; return wr_band_session_stop(&c->session, now);
}
int wr_band_coordinator_tick(struct wr_band_coordinator *c, uint64_t now)
{
    size_t slot;
    if (!clock_ok(c, now)) return c ? failure(c) : -1;
    c->last_time = now;
    if (wr_band_session_tick(&c->session, now)) return -1;
    if (c->session.phase != WR_ACTIVE) return 0;
    if (wr_band_grants_tick(&c->grants, now) || wr_band_aging_tick(&c->aging, now)) return failure(c);
    for (slot = 0; slot < WR_BAND_CLIENT_LIMIT; ++slot) {
        struct wr_band_policy_decision d;
        struct wr_band_client *client = &c->clients.entries[slot];
        struct wr_grant_slot *g = &c->grants.slots[slot];
        uint64_t last;
        int pending, started;
        if (!client->used || c->aging.pending[slot].active) continue;
        pending = g->used && (g->radio[0].phase != WR_GRANT_NONE || g->radio[1].phase != WR_GRANT_NONE);
        last = client->last_seen[0] > client->last_seen[1] ? client->last_seen[0] : client->last_seen[1];
        if (!pending && now >= c->next_age[slot] && now - last >= WR_AGING_IDLE_MS) {
            started = wr_band_aging_begin(&c->aging, slot, now);
            if (started < 0) return failure(c);
            if (started) { c->next_age[slot] = now + WR_AGING_IDLE_MS; continue; }
        }
        if (wr_band_policy_decide(&c->policy, &c->clients, slot,
                                  wr_band_grants_confirmed(&c->grants, slot), now, &d) ||
            wr_band_grants_sync(&c->grants, slot, d.desired_mask, now)) return failure(c);
    }
    return 0;
}
int wr_band_coordinator_event(struct wr_band_coordinator *c, size_t radio,
                              const struct wr_band_event *e, uint64_t now)
{
    size_t i;
    int slot, result;
    if (!clock_ok(c, now) || !e || radio >= 2) return c ? failure(c) : -1;
    c->last_time = now;
    if (wr_band_session_event(&c->session, radio, e, now)) return failure(c);
    if (c->session.phase != WR_ACTIVE) return 0;
    if (e->type == WR_EVENT_GRANT) {
        result = wr_band_grants_event(&c->grants, radio, e, now);
        return result < 0 ? failure(c) : 0;
    }
    if (e->type == WR_EVENT_IDLE) {
        /* Even stale absence can describe a real removal. Invalidate before
         * aging can free/recycle the slot; invalidation is not client activity. */
        if (!e->idle_state)
            for (i = 0; i < WR_BAND_CLIENT_LIMIT; ++i)
                if (c->clients.entries[i].used && !memcmp(c->clients.entries[i].mac, e->mac, 6))
                    if (wr_band_grants_invalidate(&c->grants, i, radio, now)) return failure(c);
        result = wr_band_aging_event(&c->aging, radio, e, now);
        if (result < 0) return failure(c);
        if (result == 2) {
            memset(&c->grants.slots[e->table_index], 0, sizeof(c->grants.slots[0]));
            wr_band_policy_forget(&c->policy, e->table_index);
            c->next_age[e->table_index] = 0;
        }
        return 0;
    }
    if (e->type != WR_EVENT_CLIENT && e->type != WR_EVENT_DELETED) return 0;
    if (e->type == WR_EVENT_DELETED) {
        for (i = 0; i < WR_BAND_CLIENT_LIMIT; ++i)
            if (c->clients.entries[i].used && !memcmp(c->clients.entries[i].mac, e->mac, 6)) break;
        if (i == WR_BAND_CLIENT_LIMIT) return 0;
    }
    slot = wr_band_clients_observe(&c->clients, radio, e, now);
    if (slot < 0) return failure(c); /* Includes capacity exhaustion; do not block untracked clients. */
    if (e->type == WR_EVENT_DELETED) {
        if (wr_band_grants_invalidate(&c->grants, (size_t)slot, radio, now)) return failure(c);
        if (c->clients.radios[radio].protocol == WR_MT76X2 && c->clients.radios[radio].band == 1)
            if (wr_band_policy_legacy_kick(&c->policy, &c->clients, radio, (size_t)slot, now)) return failure(c);
    } else if (wr_band_grants_auth(&c->grants, (size_t)slot, radio, e, now) < 0) return failure(c);
    return 0;
}
