#ifndef WR_DEVICE_RADIO_QUERY_H
#define WR_DEVICE_RADIO_QUERY_H
#include <sys/socket.h>
#include <linux/wireless.h>
#include "radio-table.h"
typedef int (*wr_radio_ioctl_fn)(const char *, int, struct iwreq *, void *);
/* Production caller supplies a fixed internal radio name and its ioctl wrapper. */
static inline int wr_radio_query(const char *interface, int streams,
                                wr_radio_ioctl_fn query, void *context,
                                struct wr_radio_snapshot *output)
{
    RT_802_11_MAC_TABLE table;
    struct iwreq request;
    if (!interface || !query || !output || !*interface ||
        strnlen(interface, IFNAMSIZ) >= IFNAMSIZ ||
        streams < 1 || streams > 3 || sizeof(table) > USHRT_MAX) return 0;
    wr_radio_prepare(&table);
    memset(&request, 0, sizeof(request));
    request.u.data.pointer = &table;
    request.u.data.length = sizeof(table);
    if (query(interface, RTPRIV_IOCTL_GET_MAC_TABLE_STRUCT, &request, context) < 0)
        return 0;
    return wr_radio_decode(&table, request.u.data.length, streams, output);
}
#endif
