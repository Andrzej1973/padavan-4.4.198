#include "policy.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void init(struct wr_band_policy *p, struct wr_band_clients *b, int reversed)
{
    struct wr_band_radio_config cfg[2] = {{WR_MT76X3, "ra0", 2}, {WR_MT76X2, "rai0", 1}};
    const struct wr_band_policy_config pc = {-70, 1500, 3000, 10000, 30000};
    struct wr_band_event e = {0};
    if (reversed) { struct wr_band_radio_config tmp = cfg[0]; cfg[0] = cfg[1]; cfg[1] = tmp; }
    assert(wr_band_clients_init(b, cfg) == 0);
    assert(wr_band_policy_init(p, &pc, 0) == 0);
    e.type = WR_EVENT_CLIENT; e.band = 2; e.mac[0] = 2; e.mac[5] = 1;
    assert(wr_band_clients_observe(b, reversed ? 1 : 0, &e, 0) == 0);
}
int main(void)
{
    struct wr_band_policy p; struct wr_band_clients b; struct wr_band_policy_decision d;
    struct wr_band_event e = {0};
    const struct wr_band_policy_config bad = {-20, 1500, 3000, 10000, 30000};
    unsigned order;
    assert(wr_band_policy_init(&p, &bad, 0) == -1);
    for (order = 0; order < 2; ++order) {
        size_t two = order ? 1 : 0, five = 1 - two;
        uint8_t two_bit = (uint8_t)(1u << two), five_bit = (uint8_t)(1u << five);
        init(&p, &b, (int)order);
        assert(wr_band_policy_decide(&p, &b, 0, 0, 1499, &d) == 0 && !d.desired_mask);
        assert(wr_band_policy_decide(&p, &b, 0, 0, 1500, &d) == 0 && d.desired_mask == two_bit);
        init(&p, &b, (int)order);
        e.type = WR_EVENT_CLIENT; e.band = 1; e.mac[0] = 2; e.mac[5] = 1;
        e.rssi_count = 1; e.rssi[0] = -65;
        assert(wr_band_clients_observe(&b, five, &e, 1) == 0);
        assert(wr_band_policy_decide(&p, &b, 0, 0, 1, &d) == 0 && d.desired_mask == five_bit);
        assert(wr_band_policy_decide(&p, &b, 0, five_bit, 1500, &d) == 0 && d.desired_mask == five_bit);
        assert(wr_band_policy_decide(&p, &b, 0, five_bit, 3000, &d) == 0 && d.desired_mask == 3);
        /* Existing 2G connection is not revoked on a strong 5G observation. */
        assert(wr_band_policy_decide(&p, &b, 0, two_bit, 3001, &d) == 0 && d.desired_mask == 3);
        b.entries[0].record_needs_sync[two] = 1;
        assert(wr_band_policy_decide(&p, &b, 0, 3, 3002, &d) == 0 && d.reconcile_mask == two_bit);
        /* Weak/stale 5G should not indefinitely hold a 2G-only connection. */
        b.entries[0].best_rssi[five] = -85;
        assert(wr_band_policy_decide(&p, &b, 0, 0, 3003, &d) == 0 && d.desired_mask == two_bit);
        b.entries[0].best_rssi[five] = -65;
        assert(wr_band_policy_decide(&p, &b, 0, 0, 10002, &d) == 0 && d.desired_mask == two_bit);
        /* Legacy deletion produces a cooldown even with still-strong samples. */
        assert(wr_band_policy_legacy_kick(&p, &b, five, 0, 10003) == 0);
        b.entries[0].last_rssi[five] = 10003;
        assert(wr_band_policy_decide(&p, &b, 0, 0, 10003, &d) == 0 && d.desired_mask == two_bit);
        b.entries[0].last_rssi[five] = 40002;
        assert(wr_band_policy_decide(&p, &b, 0, 0, 40002, &d) == 0 && d.desired_mask == two_bit);
        assert(wr_band_policy_decide(&p, &b, 0, 0, 40003, &d) == 0 && d.desired_mask == 3);
        assert(wr_band_policy_legacy_kick(&p, &b, two, 0, 40003) == -1);
        d.desired_mask = 99;
        assert(wr_band_policy_decide(&p, &b, 0, 0, 40002, &d) == -1 && d.desired_mask == 99);
        assert(wr_band_policy_decide(&p, &b, 0, 4, 40004, &d) == -1);
        assert(wr_band_policy_decide(&p, &b, 64, 0, 40004, &d) == -1);
        assert(wr_band_policy_legacy_kick(&p, &b, five, 0, UINT64_MAX) == -1);
        /* Recycled identity cannot inherit another client's cooldown. */
        assert(wr_band_policy_legacy_kick(&p, &b, five, 0, 40004) == 0);
        b.entries[0].mac[5] = 2; b.entries[0].first_seen = 40004;
        assert(wr_band_policy_decide(&p, &b, 0, 0, 40004, &d) == 0 && d.desired_mask == five_bit);
        wr_band_policy_forget(&p, 0); assert(!p.slots[0].used);
        /* 5G-only observation gets a bounded fallback when RSSI is unknown. */
        init(&p, &b, (int)order);
        b.entries[0].seen[two] = 0; b.entries[0].seen[five] = 1;
        assert(wr_band_policy_decide(&p, &b, 0, 0, 2999, &d) == 0 && !d.desired_mask);
        assert(wr_band_policy_decide(&p, &b, 0, 0, 3000, &d) == 0 && d.desired_mask == five_bit);
    }
    puts("PASS: preconnection 5G preference, bounded fallback, existing grants, stale RSSI, legacy kick cooldown, reconciliation, radio order and slot reuse; no driver I/O");
    return 0;
}
