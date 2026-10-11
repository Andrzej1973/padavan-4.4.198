#ifndef WR_DEVICE_RADIO_TABLE_H
#define WR_DEVICE_RADIO_TABLE_H
/* Caller supplies the actual RT_802_11_MAC_TABLE/ENTRY declarations. */
#include <limits.h>
#include <stddef.h>
#include <string.h>
#define WR_RADIO_LIMIT 116
/* Largest table in the pinned driver family; entry ABI is checked separately. */
struct wr_radio_wire_table {
    unsigned long Num;
    RT_802_11_MAC_ENTRY Entry[WR_RADIO_LIMIT];
};
struct wr_radio_client {
    unsigned char mac[6];
    unsigned char ap_index;
    int rssi;
};
struct wr_radio_snapshot {
    size_t count;
    struct wr_radio_client clients[WR_RADIO_LIMIT];
};
static inline void wr_radio_prepare(RT_802_11_MAC_TABLE *table)
{
    memset(table, 0, sizeof(*table));
    /* MT76x3 allocation failure can leave input length unchanged. */
    table->Num = ULONG_MAX;
}
static inline int wr_radio_decode_entries(unsigned long count,
                                 const RT_802_11_MAC_ENTRY *entries,
                                 size_t capacity, int streams,
                                 struct wr_radio_snapshot *output)
{
    struct wr_radio_snapshot candidate;
    size_t i, j;
    if (!entries || !output || capacity > WR_RADIO_LIMIT || streams < 1 || streams > 3)
        return 0;
    if (count > capacity || count > WR_RADIO_LIMIT) return 0;
    memset(&candidate, 0, sizeof(candidate));
    for (i = 0; i < count; i++) {
        const RT_802_11_MAC_ENTRY *entry = &entries[i];
        struct wr_radio_client *client = &candidate.clients[i];
        int any = 0, rssi = -127;
        signed char values[3];
        if (entry->Addr[0] & 1) return 0;
        for (j = 0; j < 6; j++) any |= entry->Addr[j];
        if (!any) return 0;
        for (j = 0; j < i; j++)
            if (!memcmp(candidate.clients[j].mac, entry->Addr, 6)) return 0;
        values[0] = (signed char)entry->AvgRssi0;
        values[1] = (signed char)entry->AvgRssi1;
        values[2] = (signed char)entry->AvgRssi2;
        for (j = 0; j < (size_t)streams; j++) {
            if (values[j] > 0 || values[j] == -128) return 0;
            if (values[j] && values[j] > rssi) rssi = values[j];
        }
        memcpy(client->mac, entry->Addr, 6);
        client->ap_index = entry->ApIdx;
        client->rssi = rssi; /* -127 is unknown; UI must not label it measured. */
    }
    candidate.count = count;
    *output = candidate;
    return 1;
}
static inline int wr_radio_decode(const RT_802_11_MAC_TABLE *table,
                                 size_t length, int streams,
                                 struct wr_radio_snapshot *output)
{
    if (!table || length != sizeof(*table)) return 0;
    return wr_radio_decode_entries(table->Num, table->Entry,
        sizeof(table->Entry) / sizeof(table->Entry[0]), streams, output);
}
static inline int wr_radio_decode_wire(const struct wr_radio_wire_table *table,
                                      size_t length, int streams,
                                      struct wr_radio_snapshot *output)
{
    size_t header = offsetof(struct wr_radio_wire_table, Entry), capacity;
    if (!table || length < header || length > sizeof(*table) ||
        (length - header) % sizeof(table->Entry[0])) return 0;
    capacity = (length - header) / sizeof(table->Entry[0]);
    /* Pinned WR export variants; never accept an arbitrary truncated table. */
    if (capacity != 64 && capacity != 75 && capacity != 58 && capacity != 41)
        return 0;
    return wr_radio_decode_entries(table->Num, table->Entry, capacity, streams, output);
}
#endif
