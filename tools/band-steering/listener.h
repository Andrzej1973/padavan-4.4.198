#ifndef WR_BAND_LISTENER_H
#define WR_BAND_LISTENER_H
#include "framing.h"
/* Opens a nonblocking CLOEXEC kernel link-event socket. Caller closes it. */
int wr_band_listener_open(void);
/* One datagram per call; -1 preserves syscall errno, or sets EPROTO/EMSGSIZE
 * for an invalid/truncated datagram. ENOBUFS requires client state recovery.
 * Caller provides reusable storage with capacity 1..65536 bytes.
 */
int wr_band_receive(int fd, uint8_t *buffer, size_t capacity,
    const struct wr_band_route *routes, size_t count,
    wr_band_event_callback callback, void *context);
#endif
