#ifndef WR_BAND_AGING_H
#define WR_BAND_AGING_H
#include "clients.h"
#define WR_AGING_IDLE_MS 60000
#define WR_AGING_REPLY_MS 3000
struct wr_band_pending_idle {
    uint8_t active, absent_mask, mac[6];
    uint32_t cookie[2];
    uint64_t activity, deadline;
};
struct wr_band_aging {
    struct wr_band_clients *book;
    struct wr_band_pending_idle pending[WR_BAND_CLIENT_LIMIT];
    uint32_t next_cookie;
    uint64_t last_time;
    wr_band_send_callback send;
    void *context;
};
/* One event-loop owner, no reentrant callbacks. Use only in ACTIVE session,
 * with driver table indices matching client slots and the modern safe-idle
 * extension compiled. Restart this object only with a new/drained listener.
 * No blind TTL deletion or WR_DELETE commands. Cookie exhaustion fails closed.
 */
int wr_band_aging_init(struct wr_band_aging *, struct wr_band_clients *,
                       uint64_t now, wr_band_send_callback, void *);
/* 1 submitted, 0 too recent/already pending, -1 invalid/send/cookie failure. */
int wr_band_aging_begin(struct wr_band_aging *, size_t slot, uint64_t now);
/* 2 freed, 1 retained/reply accepted, 0 unrelated/stale, -1 invalid time/data.
 * record_needs_sync marks absent driver records even for expired/stale replies.
 * The steering policy must reconcile those flags before assuming a grant.
 */
int wr_band_aging_event(struct wr_band_aging *, size_t radio,
                        const struct wr_band_event *, uint64_t now);
int wr_band_aging_tick(struct wr_band_aging *, uint64_t now);
#endif
