#ifndef WR_BAND_EVENTS_H
#define WR_BAND_EVENTS_H
#include "protocol.h"
enum wr_band_event_type { WR_EVENT_CLIENT, WR_EVENT_READY, WR_EVENT_ENABLED,
                          WR_EVENT_DELETED, WR_EVENT_REJECTED, WR_EVENT_IDLE, WR_EVENT_GRANT };
struct wr_band_event {
    enum wr_band_event_type type;
    uint8_t action, frame_type, band, channel, ready, enabled;
    uint8_t mac[6];
    int8_t rssi[4];
    uint8_t rssi_count;
    uint32_t owner_pid;
    uint32_t cookie;
    uint8_t table_index, idle_state; /* 0 absent/removed, 1 MAC present, 2 error */
    uint8_t grant_state; /* 0 record absent, 1 present, 2 index/error; not association proof */
    char interface_name[16];
};
/* Complete driver payload only; caller selects protocol from event interface.
 * 1 decoded; 0 unsupported action; -1 malformed. No radio commands are issued.
 */
int wr_band_decode(enum wr_band_protocol protocol, const uint8_t *payload,
                   size_t length, struct wr_band_event *event);
#endif
