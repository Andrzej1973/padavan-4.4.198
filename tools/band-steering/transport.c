/* Pinned driver ap_ioctl.c routes RT_PRIV_IOCTL and u.data.flags to
 * RTMPAPSetInformation when OID_GET_SET_TOGGLE is set. */
#include "transport.h"
#include <errno.h>
#include <string.h>
#include <sys/ioctl.h>
#include <linux/wireless.h>

int wr_band_send(int fd, enum wr_band_protocol protocol,
                 const struct wr_band_request *request)
{
    uint8_t payload[80];
    struct iwreq wrq;
    int length;
    if (fd < 0) { errno = EBADF; return -1; }
    length = wr_band_encode(protocol, request, payload, sizeof(payload));
    if (length < 0) { errno = EINVAL; return -1; }
    memset(&wrq, 0, sizeof(wrq));
    memcpy(wrq.ifr_name, request->interface_name, strlen(request->interface_name));
    wrq.u.data.pointer = payload;
    wrq.u.data.length = (unsigned short)length;
    wrq.u.data.flags = 0x0950 | 0x8000;
    if (ioctl(fd, SIOCIWFIRSTPRIV + 1, &wrq) < 0) return -1;
    return 0;
}
