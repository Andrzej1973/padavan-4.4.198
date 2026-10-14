/* Read-only, fixed-interface station-table query; never print station identifiers. */
#include <stdio.h>
#include <errno.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include "radio-table.h"
/* Fixed read command from pinned httpd/ralink.c, not a private set ioctl. */
#define RTPRIV_IOCTL_GET_MAC_TABLE_STRUCT (SIOCIWFIRSTPRIV + 0x1F)
#include "radio-query.h"
int main(int argc, char **argv)
{
    const char *names[2] = {"ra0", "rai0"};
    int fd, band, failed = 0;
    (void)argv;
    if (argc != 1) return 2;
    fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) { puts("{\"error\":\"socket_unavailable\"}"); return 1; }
    alarm(3);
    for (band = 0; band < 2; ++band) {
        struct wr_radio_wire_table table;
        struct wr_radio_snapshot decoded;
        struct iwreq request;
        int result, saved_errno, valid;
        memset(&table, 0, sizeof(table)); table.Num = ULONG_MAX;
        memset(&request, 0, sizeof(request));
        strcpy(request.ifr_name, names[band]);
        request.u.data.pointer = &table;
        request.u.data.length = sizeof(table);
        errno = 0;
        result = ioctl(fd, RTPRIV_IOCTL_GET_MAC_TABLE_STRUCT, &request);
        saved_errno = result < 0 ? errno : 0;
        valid = result >= 0 && wr_radio_decode_wire(&table, request.u.data.length, 2, &decoded);
        printf("{\"radio\":%d,\"ioctl_result\":%d,\"errno\":%d,\"returned_bytes\":%u,\"decode_valid\":%s,\"records\":%lu}\n",
               band, result, saved_errno, (unsigned int)request.u.data.length,
               valid ? "true" : "false", valid ? (unsigned long)decoded.count : 0UL);
        if (!valid) failed = 1;
    }
    alarm(0);
    if (close(fd)) failed = 1;
    return failed;
}
