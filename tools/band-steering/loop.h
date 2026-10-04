#ifndef WR_BAND_LOOP_H
#define WR_BAND_LOOP_H
#include "coordinator.h"
#include "framing.h"
struct wr_band_loop_io {
    int (*clock)(void *, uint64_t *);
    int (*receive)(void *, wr_band_event_callback, void *);
    int (*wait)(void *, int milliseconds);
    int (*stopping)(void *);
};
/* One process owns both command socket and coordinator. Callbacks never
 * reenter the loop. Receive is nonblocking, validates sender/framing, and
 * preserves errno. Datagram/time budgets prevent event floods starving ticks.
 * 0 = both OFF acknowledgements (or never enabled); -1 = unverified failure.
 */
int wr_band_loop_run(struct wr_band_coordinator *, const struct wr_band_loop_io *, void *);
#endif
