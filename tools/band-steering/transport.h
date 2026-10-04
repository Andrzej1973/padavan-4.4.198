#ifndef WR_BAND_TRANSPORT_H
#define WR_BAND_TRANSPORT_H
#include "protocol.h"
/* Caller owns a persistent AF_INET/SOCK_DGRAM socket and process.
 * Success means ioctl submission only; the driver must acknowledge separately.
 * Returns 0 or -1 with errno. No retry is performed on interrupted commands.
 */
int wr_band_send(int socket_fd, enum wr_band_protocol protocol,
                 const struct wr_band_request *request);
#endif
