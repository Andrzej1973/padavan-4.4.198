#ifndef WR_BAND_COORDINATOR_H
#define WR_BAND_COORDINATOR_H
#include "aging.h"
#include "grants.h"
#include "policy.h"
struct wr_band_coordinator {
    struct wr_band_session session;
    struct wr_band_clients clients;
    struct wr_band_aging aging;
    struct wr_band_grants grants;
    struct wr_band_policy policy;
    uint64_t last_time, next_age[WR_BAND_CLIENT_LIMIT];
};
/* Single-owner normalized-event coordinator; no sockets/profile/UI installed.
 * Establish driver/profile exclusivity and a fresh listener before init.
 * Call fault for listener loss/truncation/ENOBUFS, and stop for normal shutdown.
 * FAILED means best-effort disable was requested, not proven hardware OFF.
 */
int wr_band_coordinator_init(struct wr_band_coordinator *, const struct wr_band_radio_config[2],
                             const struct wr_band_policy_config *, uint64_t,
                             wr_band_send_callback, void *);
int wr_band_coordinator_tick(struct wr_band_coordinator *, uint64_t);
int wr_band_coordinator_event(struct wr_band_coordinator *, size_t radio,
                              const struct wr_band_event *, uint64_t);
int wr_band_coordinator_stop(struct wr_band_coordinator *, uint64_t);
void wr_band_coordinator_fault(struct wr_band_coordinator *);
#endif
