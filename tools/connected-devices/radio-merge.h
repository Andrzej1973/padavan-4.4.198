#ifndef WR_DEVICE_RADIO_MERGE_H
#define WR_DEVICE_RADIO_MERGE_H
#include "networkmap.h"
#include "radio-table.h"
struct wr_device_radio_evidence {
    unsigned int band_mask;
    unsigned char ap_index[2];
    int rssi[2];
};
struct wr_device_joined_snapshot {
    struct wr_device_snapshot networkmap;
    struct wr_device_radio_evidence radio[WR_DEVICE_LIMIT];
};
/* Both radio snapshots must represent successful queries, including empty ones.
 * Failed queries must be handled by the caller's stale-cache policy. */
static inline int wr_device_radio_merge(const struct wr_device_snapshot *base,
                                       const struct wr_radio_snapshot *two,
                                       const struct wr_radio_snapshot *five,
                                       struct wr_device_joined_snapshot *output)
{
    struct wr_device_joined_snapshot candidate;
    const struct wr_radio_snapshot *bands[2];
    size_t band, i, j;
    if (!base || !two || !five || !output || base->count > WR_DEVICE_LIMIT ||
        two->count > WR_RADIO_LIMIT || five->count > WR_RADIO_LIMIT) return 0;
    for (i = 0; i < base->count; i++)
        if (strnlen(base->records[i].mac, sizeof(base->records[i].mac)) ==
            sizeof(base->records[i].mac)) return 0;
    memset(&candidate, 0, sizeof(candidate));
    candidate.networkmap = *base;
    bands[0] = two; bands[1] = five;
    for (band = 0; band < 2; band++) {
        for (i = 0; i < bands[band]->count; i++) {
            const struct wr_radio_client *client = &bands[band]->clients[i];
            char mac[18]; int found = 0;
            snprintf(mac, sizeof(mac), "%02X:%02X:%02X:%02X:%02X:%02X",
                     client->mac[0], client->mac[1], client->mac[2],
                     client->mac[3], client->mac[4], client->mac[5]);
            for (j = 0; j < candidate.networkmap.count; j++) {
                struct wr_device_radio_evidence *evidence = &candidate.radio[j];
                if (strcmp(candidate.networkmap.records[j].mac, mac)) continue;
                evidence->band_mask |= 1U << band;
                evidence->ap_index[band] = client->ap_index;
                evidence->rssi[band] = client->rssi;
                found = 1;
            }
            if (!found) {
                struct wr_device_record *record;
                struct wr_device_radio_evidence *evidence;
                if (candidate.networkmap.count == WR_DEVICE_LIMIT) {
                    candidate.networkmap.truncated = 1; continue;
                }
                j = candidate.networkmap.count++;
                record = &candidate.networkmap.records[j];
                memset(record, 0, sizeof(*record));
                strcpy(record->mac, mac);
                record->networkmap_stale = 1; /* No networkmap evidence for this MAC. */
                evidence = &candidate.radio[j];
                evidence->band_mask = 1U << band;
                evidence->ap_index[band] = client->ap_index;
                evidence->rssi[band] = client->rssi;
            }
        }
    }
    *output = candidate;
    return 1;
}
#endif
