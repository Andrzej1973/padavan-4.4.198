#ifndef WR_BAND_SESSION_H
#define WR_BAND_SESSION_H
#include "events.h"
enum wr_band_phase { WR_QUERYING, WR_ENABLING, WR_ACTIVE, WR_STOPPING, WR_STOPPED, WR_FAILED };
struct wr_band_radio_config { enum wr_band_protocol protocol; char name[16]; uint8_t band; };
typedef int (*wr_band_send_callback)(size_t radio, enum wr_band_protocol,
                                    const struct wr_band_request *, void *);
struct wr_band_session {
    enum wr_band_phase phase;
    struct wr_band_radio_config radios[2];
    uint8_t ready[2], enabled[2], attempted[2], channel[2];
    uint8_t off_acknowledged[2];
    uint64_t deadline, next_query, next_heartbeat, last_tick, last_time, last_status[2];
    wr_band_send_callback send;
    void *context;
};
/* Clock values are monotonic milliseconds. All calls stay in one process.
 * init/tick may submit enable commands: use only after driver/profile/policy
 * preconditions are established. This module is not installed in firmware yet.
 */
int wr_band_session_init(struct wr_band_session *, const struct wr_band_radio_config[2],
                         uint64_t now, wr_band_send_callback, void *);
int wr_band_session_tick(struct wr_band_session *, uint64_t now);
int wr_band_session_event(struct wr_band_session *, size_t radio,
                          const struct wr_band_event *, uint64_t now);
int wr_band_session_stop(struct wr_band_session *, uint64_t now);
/* Exclusive-owner recovery: issue OFF to both radios without enabling either.
 * Success of this call means sent only; both acknowledgements are required. */
int wr_band_session_quiesce(struct wr_band_session *, uint64_t now);
int wr_band_session_off_confirmed(const struct wr_band_session *);
void wr_band_session_fault(struct wr_band_session *);
#endif
