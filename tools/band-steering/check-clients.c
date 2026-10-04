#include "clients.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void)
{
    struct wr_band_clients book;
    const struct wr_band_radio_config cfg[2] = {{WR_MT76X3, "ra0", 2}, {WR_MT76X2, "rai0", 1}};
    struct wr_band_event e = {0};
    unsigned i;
    assert(wr_band_clients_init(&book, cfg) == 0);
    e.type = WR_EVENT_CLIENT; e.band = 2; e.mac[0] = 2; e.mac[5] = 1;
    e.rssi_count = 4; e.rssi[0] = -128; e.rssi[1] = -70; e.rssi[2] = -65; e.rssi[3] = 0;
    assert(wr_band_clients_observe(&book, 0, &e, 1) == 0);
    assert(book.entries[0].rssi_valid[0] && book.entries[0].best_rssi[0] == -65);
    e.band = 1; e.rssi_count = 3;
    assert(wr_band_clients_observe(&book, 1, &e, 2) == 0);
    assert(book.entries[0].seen[0] && book.entries[0].seen[1]);
    assert(book.entries[0].connection[1] == WR_CONNECTION_UNKNOWN);
    e.band = 2; e.frame_type = 2; e.rssi_count = 0;
    assert(wr_band_clients_observe(&book, 0, &e, 3) == 0 && book.entries[0].connection[0] == WR_CONNECTED);
    assert(book.entries[0].best_rssi[0] == -65 && book.entries[0].last_rssi[0] == 1);
    e.frame_type = 1;
    assert(wr_band_clients_observe(&book, 0, &e, 4) == 0 && book.entries[0].connection[0] == WR_DISCONNECTED);
    e.frame_type = 0; e.rssi_count = 4; memset(e.rssi, 0x80, sizeof(e.rssi));
    assert(wr_band_clients_observe(&book, 0, &e, 5) == 0 && !book.entries[0].rssi_valid[0]);
    assert(wr_band_clients_observe(&book, 0, &e, 4) == -1);
    e.mac[0] = 3; assert(wr_band_clients_observe(&book, 0, &e, 6) == -1); e.mac[0] = 2;
    e.rssi_count = 5; assert(wr_band_clients_observe(&book, 0, &e, 6) == -1); e.rssi_count = 0;
    for (i = 2; i <= 64; ++i) {
        e.mac[5] = (uint8_t)i;
        assert(wr_band_clients_observe(&book, 0, &e, 10 + i) == (int)i - 1);
    }
    e.mac[5] = 65;
    assert(wr_band_clients_observe(&book, 0, &e, 100) == -2);
    e.mac[5] = 1;
    assert(wr_band_clients_observe(&book, 0, &e, 100) == 0);
    e.type = WR_EVENT_DELETED;
    assert(wr_band_clients_observe(&book, 1, &e, 101) == 0 && book.entries[0].connection[1] == WR_CONNECTION_UNKNOWN);
    puts("PASS: bounded 64-client observations, dual-radio identity, RSSI validity and connection semantics; no driver commands");
    return 0;
}
