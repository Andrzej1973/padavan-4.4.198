#ifndef WR_BAND_POLICY_H
#define WR_BAND_POLICY_H
#include "clients.h"
struct wr_band_policy_config {
    int8_t prefer_5g_rssi;
    uint32_t hold_2g_ms, fallback_ms, rssi_fresh_ms, kick_cooldown_ms;
};
struct wr_band_policy_slot {
    uint8_t used, mac[6];
    uint64_t birth, block_5g_until;
};
struct wr_band_policy {
    struct wr_band_policy_config config;
    struct wr_band_policy_slot slots[WR_BAND_CLIENT_LIMIT];
    uint64_t last_time;
};
struct wr_band_policy_decision {
    uint8_t desired_mask; /* bit by configured radio index, not band enum */
    uint8_t reconcile_mask; /* desired records reported absent by idle checks */
};
int wr_band_policy_init(struct wr_band_policy *, const struct wr_band_policy_config *, uint64_t now);
/* This is a decision engine, not driver I/O. confirmed_mask must reflect
 * actual driver state, not an ioctl return (handlers can ignore commands).
 * Pending command deduplication/readback belongs to the future controller.
 * Existing grants are retained; this module never requests deauthentication.
 */
int wr_band_policy_decide(struct wr_band_policy *, const struct wr_band_clients *,
                          size_t slot, uint8_t confirmed_mask, uint64_t now,
                          struct wr_band_policy_decision *);
/* Call for legacy 5G CLI_DEL before the next decision. Clear the controller's
 * confirmed 5G grant, and record observation through clients_observe as well.
 */
int wr_band_policy_legacy_kick(struct wr_band_policy *, const struct wr_band_clients *,
                               size_t radio, size_t slot, uint64_t now);
void wr_band_policy_forget(struct wr_band_policy *, size_t slot);
#endif
