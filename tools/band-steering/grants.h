#ifndef WR_BAND_GRANTS_H
#define WR_BAND_GRANTS_H
#include "clients.h"
enum wr_grant_phase { WR_GRANT_NONE, WR_GRANT_QUERYING, WR_GRANT_AFTER_ADD };
struct wr_grant_radio {
    enum wr_grant_phase phase;
    uint8_t wanted, confirmed;
    uint32_t cookie;
    uint64_t activity, deadline, verified_at;
};
struct wr_grant_slot {
    uint8_t used, mac[6];
    uint64_t birth;
    struct wr_grant_radio radio[2];
};
struct wr_band_grants {
    struct wr_band_clients *book;
    struct wr_grant_slot slots[WR_BAND_CLIENT_LIMIT];
    uint32_t next_cookie;
    uint64_t last_time;
    uint8_t failed;
    wr_band_send_callback send;
    void *context;
};
/* Isolated controller, one non-reentrant event-loop owner in ACTIVE session.
 * Requires prepared grant handlers. Pause sync for a slot during idle aging;
 * deliver idle absence and driver deletion through invalidate before resync.
 * Recycle client slots only after the dual-radio absence proof. Fresh/drained
 * event listener required on init. confirmed means record presence, not link.
 */
int wr_band_grants_init(struct wr_band_grants *, struct wr_band_clients *, uint64_t,
                        wr_band_send_callback, void *);
int wr_band_grants_sync(struct wr_band_grants *, size_t slot, uint8_t desired_mask, uint64_t);
/* 1 matching proof/progression; 0 stale/unrelated; -1 malformed/fatal. */
int wr_band_grants_event(struct wr_band_grants *, size_t radio, const struct wr_band_event *, uint64_t);
int wr_band_grants_tick(struct wr_band_grants *, uint64_t);
int wr_band_grants_invalidate(struct wr_band_grants *, size_t slot, size_t radio, uint64_t);
uint8_t wr_band_grants_confirmed(const struct wr_band_grants *, size_t slot);
/* Send failure, timeout, index error or failed post-add proof sets failed.
 * The owner must stop/disable the session; it must not claim recovery merely
 * from ioctl success. Modern associated-entry reauthentication is separate.
 */
#endif
