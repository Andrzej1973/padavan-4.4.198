#ifndef WR_BAND_FRAMING_H
#define WR_BAND_FRAMING_H
#include "events.h"
struct wr_band_route { uint32_t ifindex; enum wr_band_protocol protocol; };
typedef void (*wr_band_event_callback)(size_t radio, const struct wr_band_event *, void *);
/* MIPS32 little-endian kernel RTM_NEWLINK/Wireless Extensions datagrams.
 * Caller must verify recvmsg sender is kernel and MSG_TRUNC is absent.
 * Returns event count or -1. Validates the whole datagram before callbacks.
 */
int wr_band_parse_netlink(const uint8_t *data, size_t length,
    const struct wr_band_route *routes, size_t route_count,
    wr_band_event_callback callback, void *context);
#endif
