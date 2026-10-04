#include "clients.h"
#include <string.h>
int wr_band_clients_init(struct wr_band_clients *book, const struct wr_band_radio_config cfg[2])
{
    size_t i;
    if (!book || !cfg) return -1;
    for (i = 0; i < 2; ++i)
        if ((cfg[i].protocol != WR_MT76X2 && cfg[i].protocol != WR_MT76X3) ||
            (cfg[i].band != 1 && cfg[i].band != 2) ||
            !memchr(cfg[i].name, 0, sizeof(cfg[i].name))) return -1;
    if (cfg[0].band == cfg[1].band) return -1;
    memset(book, 0, sizeof(*book)); memcpy(book->radios, cfg, sizeof(book->radios));
    return 0;
}
int wr_band_clients_observe(struct wr_band_clients *book, size_t radio,
                            const struct wr_band_event *event, uint64_t now)
{
    size_t i, slot = WR_BAND_CLIENT_LIMIT, free_slot = WR_BAND_CLIENT_LIMIT;
    struct wr_band_client *client;
    unsigned any = 0;
    if (!book || !event || radio >= 2 || now < book->last_time || event->rssi_count > 4 ||
        (event->type != WR_EVENT_CLIENT && event->type != WR_EVENT_DELETED)) return -1;
    if (event->type == WR_EVENT_CLIENT && event->band != book->radios[radio].band) return -1;
    for (i = 0; i < 6; ++i) any |= event->mac[i];
    if (!any || (event->mac[0] & 1)) return -1;
    for (i = 0; i < WR_BAND_CLIENT_LIMIT; ++i) {
        if (book->entries[i].used && memcmp(book->entries[i].mac, event->mac, 6) == 0) slot = i;
        if (!book->entries[i].used && free_slot == WR_BAND_CLIENT_LIMIT) free_slot = i;
    }
    if (slot == WR_BAND_CLIENT_LIMIT) {
        if (event->type == WR_EVENT_DELETED) return -1;
        if (free_slot == WR_BAND_CLIENT_LIMIT) return -2;
        slot = free_slot;
        book->entries[slot].used = 1;
        memcpy(book->entries[slot].mac, event->mac, 6);
        book->entries[slot].first_seen = now;
    }
    book->last_time = now;
    client = &book->entries[slot]; client->seen[radio] = 1; client->last_seen[radio] = now;
    if (event->type == WR_EVENT_DELETED) {
        /* A deleted legacy steering entry does not prove link disconnection. */
        client->connection[radio] = WR_CONNECTION_UNKNOWN;
        return (int)slot;
    }
    if (book->radios[radio].protocol == WR_MT76X3) {
        if (event->frame_type == 2) client->connection[radio] = WR_CONNECTED;
        else if (event->frame_type == 1) client->connection[radio] = WR_DISCONNECTED;
    }
    if (event->rssi_count) {
        client->rssi_valid[radio] = 0; client->last_rssi[radio] = now;
        for (i = 0; i < event->rssi_count; ++i) {
            int8_t sample = event->rssi[i];
            /* mt76x3 fills unused chains with 0x80; zero is not a measured RSSI. */
            if (sample == -128 || sample >= 0) continue;
            if (!client->rssi_valid[radio] || sample > client->best_rssi[radio])
                client->best_rssi[radio] = sample;
            client->rssi_valid[radio] = 1;
        }
    }
    return (int)slot;
}
