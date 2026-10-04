#include "policy.h"
#include <string.h>
int wr_band_policy_init(struct wr_band_policy *p, const struct wr_band_policy_config *cfg, uint64_t now)
{
    if (!p || !cfg || cfg->prefer_5g_rssi < -90 || cfg->prefer_5g_rssi > -30 ||
        cfg->hold_2g_ms > 10000 || cfg->fallback_ms < cfg->hold_2g_ms ||
        cfg->fallback_ms > 10000 || !cfg->rssi_fresh_ms || cfg->rssi_fresh_ms > 60000 ||
        cfg->kick_cooldown_ms < 1000 || cfg->kick_cooldown_ms > 600000) return -1;
    memset(p, 0, sizeof(*p)); p->config = *cfg; p->last_time = now; return 0;
}
static struct wr_band_policy_slot *slot_state(struct wr_band_policy *p,
                                               const struct wr_band_client *c, size_t slot)
{
    struct wr_band_policy_slot *s = &p->slots[slot];
    if (!s->used || s->birth != c->first_seen || memcmp(s->mac, c->mac, 6)) {
        memset(s, 0, sizeof(*s)); s->used = 1; s->birth = c->first_seen;
        memcpy(s->mac, c->mac, 6);
    }
    return s;
}
void wr_band_policy_forget(struct wr_band_policy *p, size_t slot)
{
    if (p && slot < WR_BAND_CLIENT_LIMIT) memset(&p->slots[slot], 0, sizeof(p->slots[slot]));
}
int wr_band_policy_legacy_kick(struct wr_band_policy *p, const struct wr_band_clients *b,
                               size_t radio, size_t slot, uint64_t now)
{
    struct wr_band_policy_slot *s;
    if (!p || !b || radio >= 2 || slot >= WR_BAND_CLIENT_LIMIT || !b->entries[slot].used ||
        b->radios[radio].protocol != WR_MT76X2 || b->radios[radio].band != 1 ||
        now < p->last_time || now < b->last_time || now < b->entries[slot].first_seen ||
        now > UINT64_MAX - p->config.kick_cooldown_ms) return -1;
    s = slot_state(p, &b->entries[slot], slot);
    s->block_5g_until = now + p->config.kick_cooldown_ms; p->last_time = now;
    return 0;
}
int wr_band_policy_decide(struct wr_band_policy *p, const struct wr_band_clients *b,
                          size_t slot, uint8_t confirmed, uint64_t now,
                          struct wr_band_policy_decision *out)
{
    struct wr_band_policy_slot *s;
    const struct wr_band_client *c;
    struct wr_band_policy_decision d = {0};
    size_t five, two, i;
    uint64_t age;
    int fresh, strong, blocked;
    if (!p || !b || !out || slot >= WR_BAND_CLIENT_LIMIT || (confirmed & ~3u) ||
        now < p->last_time || now < b->last_time || !b->entries[slot].used ||
        b->radios[0].band == b->radios[1].band ||
        (b->radios[0].band != 1 && b->radios[0].band != 2) ||
        (b->radios[1].band != 1 && b->radios[1].band != 2)) return -1;
    c = &b->entries[slot];
    if (now < c->first_seen || now < c->last_rssi[0] || now < c->last_rssi[1]) return -1;
    five = b->radios[0].band == 1 ? 0 : 1; two = 1 - five;
    age = now - c->first_seen;
    s = slot_state(p, c, slot); p->last_time = now;
    blocked = now < s->block_5g_until;
    fresh = c->rssi_valid[five] && now - c->last_rssi[five] <= p->config.rssi_fresh_ms;
    strong = fresh && c->best_rssi[five] >= p->config.prefer_5g_rssi;
    d.desired_mask = confirmed;
    /* A legacy kick already revoked the grant; avoid immediately recreating it.
     * Clients can still try 2.4G. This is not a command to delete a 5G grant. */
    if (blocked) {
        d.desired_mask &= (uint8_t)~(1u << five);
        d.desired_mask |= (uint8_t)(1u << two);
    } else if (c->seen[five] && (strong || (!c->seen[two] && age >= p->config.fallback_ms))) {
        d.desired_mask |= (uint8_t)(1u << five);
    }
    if (c->seen[two] && age >= p->config.hold_2g_ms &&
        (!strong || blocked || age >= p->config.fallback_ms))
        d.desired_mask |= (uint8_t)(1u << two);
    for (i = 0; i < 2; ++i)
        if (c->record_needs_sync[i] && (d.desired_mask & (1u << i)))
            d.reconcile_mask |= (uint8_t)(1u << i);
    *out = d; return 0;
}
