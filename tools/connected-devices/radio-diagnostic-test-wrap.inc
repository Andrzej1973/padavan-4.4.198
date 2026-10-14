/* Native fixture only; never link this file into the device diagnostic. */
#include <assert.h>
#include <stdarg.h>
#include <stdlib.h>
int __wrap_socket(int domain, int type, int protocol)
{
    assert(domain == AF_INET && type == SOCK_DGRAM && protocol == 0);
    return 99;
}
int __wrap_close(int fd) { assert(fd == 99); return 0; }
int __wrap_ioctl(int fd, unsigned long command, ...)
{
    va_list arguments;
    struct iwreq *request;
    struct wr_radio_wire_table *table;
    const char *mode = getenv("WR_DIAGNOSTIC_TEST_MODE");
    assert(fd == 99 && command == RTPRIV_IOCTL_GET_MAC_TABLE_STRUCT);
    va_start(arguments, command);
    request = va_arg(arguments, struct iwreq *);
    va_end(arguments);
    assert(!strcmp(request->ifr_name, "ra0") || !strcmp(request->ifr_name, "rai0"));
    assert(request->u.data.length == sizeof(struct wr_radio_wire_table));
    table = request->u.data.pointer;
    assert(table->Num == ULONG_MAX);
    if (mode && !strcmp(mode, "error")) { errno = EOPNOTSUPP; return -1; }
    table->Num = 0;
    request->u.data.length = mode && !strcmp(mode, "short") ? 0 : sizeof(RT_802_11_MAC_TABLE);
    return 0;
}
