#ifndef WR_BAND_CLIENTS_H
#define WR_BAND_CLIENTS_H
#include "session.h"
#define WR_BAND_CLIENT_LIMIT 64
enum wr_band_connection { WR_CONNECTION_UNKNOWN, WR_DISCONNECTED, WR_CONNECTED };
struct wr_band_client {
    uint8_t used, mac[6], seen[2], rssi_valid[2];
    int8_t best_rssi[2];
    enum wr_band_connection connection[2];
    uint64_t first_seen, last_seen[2], last_rssi[2];
};
struct wr_band_clients {
    struct wr_band_radio_config radios[2];
    struct wr_band_client entries[WR_BAND_CLIENT_LIMIT];
    uint64_t last_time;
};
int wr_band_clients_init(struct wr_band_clients *, const struct wr_band_radio_config[2]);
/* Returns slot 0..63, -1 invalid/unrelated event, -2 capacity exhausted.
 * No driver commands or timeout-based deletion. Legacy connection remains
 * unknown until a separate authoritative connection check is implemented.
 */
int wr_band_clients_observe(struct wr_band_clients *, size_t radio,
                            const struct wr_band_event *, uint64_t now);
#endif
