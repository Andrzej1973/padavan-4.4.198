#include "transport.h"
#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <string.h>
#include <linux/wireless.h>
#include <stdio.h>
static int calls, fail_ioctl, expected_length, expected_action;
int __wrap_ioctl(int fd, unsigned long command, ...)
{
    va_list args;
    struct iwreq *wrq;
    va_start(args, command);
    wrq = va_arg(args, struct iwreq *);
    va_end(args);
    ++calls;
    assert(fd == 42 && command == SIOCIWFIRSTPRIV + 1);
    assert(strcmp(wrq->ifr_name, "ra0") == 0);
    assert(wrq->u.data.flags == 0x8950);
    assert(wrq->u.data.length == expected_length);
    assert(((unsigned char *)wrq->u.data.pointer)[0] == expected_action);
    if (fail_ioctl) { errno = EINTR; return -1; }
    return 0;
}
int main(void)
{
    struct wr_band_request r = {0};
    r.command = WR_QUERY; r.interface_name = "ra0";
    expected_length = 80; expected_action = 8;
    assert(wr_band_send(42, WR_MT76X3, &r) == 0 && calls == 1);
    expected_length = 32; expected_action = 6;
    assert(wr_band_send(42, WR_MT76X2, &r) == 0 && calls == 2);
    fail_ioctl = 1;
    assert(wr_band_send(42, WR_MT76X2, &r) == -1 && errno == EINTR && calls == 3);
    assert(wr_band_send(-1, WR_MT76X2, &r) == -1 && errno == EBADF && calls == 3);
    r.interface_name = "invalid/name";
    assert(wr_band_send(42, WR_MT76X2, &r) == -1 && errno == EINVAL && calls == 3);
    puts("PASS: ioctl fields, protocol selection, error propagation; no real ioctl executed");
    return 0;
}
