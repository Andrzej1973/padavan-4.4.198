/* Message layout: pinned c25283e9 driver declarations, target ABI runs
 * 37177074123 and 37177297548. Explicit byte encoding avoids host ABI padding.
 * This original adapter implements the documented wire fields independently.
 */
#include "protocol.h"
#include <string.h>

static int valid_interface(const char *name)
{
    size_t n;
    if (!name) return 0;
    for (n = 0; n < 16 && name[n]; ++n) {
        unsigned char c = (unsigned char)name[n];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.')) return 0;
    }
    return n > 0 && n < 16;
}

int wr_band_encode(enum wr_band_protocol protocol, const struct wr_band_request *r,
                   uint8_t *out, size_t capacity)
{
    size_t size;
    uint8_t action;
    if (!r || !out || !valid_interface(r->interface_name)) return -1;
    if (protocol == WR_MT76X2) size = 32;
    else if (protocol == WR_MT76X3) size = 80;
    else return -1;
    if (capacity < size || r->enabled > 1) return -1;
    switch (r->command) {
    case WR_QUERY: action = protocol == WR_MT76X2 ? 6 : 8; break;
    case WR_ENABLE: action = protocol == WR_MT76X2 ? 11 : 12; break;
    case WR_ADD: action = 2; break;
    case WR_DELETE: action = 3; break;
    case WR_HEARTBEAT:
        if (protocol != WR_MT76X3) return -1;
        action = 16; /* HEARTBEAT_MONITOR in the pinned mt76x3 ACTION_CODE. */
        break;
    default: return -1;
    }
    memset(out, 0, size);
    out[0] = action;
    if (protocol == WR_MT76X2) {
        if (r->command == WR_ENABLE) out[3] = r->enabled;
        if (r->command == WR_ADD || r->command == WR_DELETE) {
            out[2] = r->table_index;
            memcpy(out + 24, r->mac, 6);
        }
    } else {
        if (r->command == WR_QUERY || r->command == WR_HEARTBEAT)
            memcpy(out + 8, r->interface_name, strlen(r->interface_name));
        if (r->command == WR_ENABLE) {
            out[8] = r->band;
            out[9] = r->channel;
            out[10] = r->enabled;
            out[11] = r->mode;
            memcpy(out + 12, r->interface_name, strlen(r->interface_name));
        }
        if (r->command == WR_ADD || r->command == WR_DELETE) {
            out[8] = r->table_index;
            memcpy(out + 9, r->mac, 6);
        }
    }
    return (int)size;
}
