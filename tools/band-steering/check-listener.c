#include "listener.h"
#include <assert.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
static int failure, mode, closes, calls;
int __wrap_socket(int family, int type, int protocol)
{
    assert(family == AF_NETLINK && protocol == NETLINK_ROUTE);
    assert(type == (SOCK_RAW | SOCK_NONBLOCK | SOCK_CLOEXEC));
    if (failure == 1) { errno = ENFILE; return -1; }
    return 42;
}
int __wrap_setsockopt(int fd, int level, int option, const void *value, socklen_t length)
{
    assert(fd == 42 && level == SOL_SOCKET && option == SO_RCVBUF);
    assert(length == sizeof(int) && *(const int *)value == 262144);
    if (failure == 2) { errno = EACCES; return -1; }
    return 0;
}
int __wrap_bind(int fd, const struct sockaddr *address, socklen_t length)
{
    const struct sockaddr_nl *nl = (const struct sockaddr_nl *)address;
    assert(fd == 42 && length == sizeof(*nl));
    assert(nl->nl_family == AF_NETLINK && nl->nl_pid == 0 && nl->nl_groups == RTMGRP_LINK);
    if (failure == 3) { errno = EADDRINUSE; return -1; }
    return 0;
}
int __wrap_close(int fd) { assert(fd == 42); ++closes; errno = EBADF; return -1; }
ssize_t __wrap_recvmsg(int fd, struct msghdr *message, int flags)
{
    struct sockaddr_nl *sender = message->msg_name;
    uint8_t *p = message->msg_iov[0].iov_base;
    assert(fd == 42 && flags == 0 && message->msg_iovlen == 1);
    assert(message->msg_namelen == sizeof(*sender) && message->msg_iov[0].iov_len == 128);
    if (mode == 1) { errno = EAGAIN; return -1; }
    if (mode == 2) { errno = ENOBUFS; return -1; }
    memset(p, 0, 76);
    p[0] = 76; p[4] = 16; p[20] = 5;
    p[32] = 44; p[34] = 11; p[36] = 40; p[38] = 2; p[39] = 0x8c;
    p[40] = 32; p[42] = 0x50; p[43] = 9; p[44] = 11; p[47] = 1;
    sender->nl_family = AF_NETLINK; sender->nl_pid = 0;
    if (mode == 3) message->msg_flags = MSG_TRUNC;
    if (mode == 4) sender->nl_pid = 99;
    if (mode == 5) message->msg_namelen = 0;
    if (mode == 6) return 0;
    if (mode == 7) return 129;
    if (mode == 8) p[0] = 0;
    return 76;
}
static void event(size_t radio, const struct wr_band_event *e, void *ctx)
{
    assert(radio == 0 && e->type == WR_EVENT_ENABLED && e->enabled == 1 && ctx == &calls);
    ++calls;
}
int main(void)
{
    uint8_t buffer[128];
    struct wr_band_route route = {5, WR_MT76X2};
    int n;
    assert(wr_band_listener_open() == 42);
    failure = 1; assert(wr_band_listener_open() == -1 && errno == ENFILE && closes == 0);
    failure = 2; assert(wr_band_listener_open() == -1 && errno == EACCES && closes == 1);
    failure = 3; assert(wr_band_listener_open() == -1 && errno == EADDRINUSE && closes == 2);
    assert(wr_band_receive(42, buffer, sizeof(buffer), &route, 1, event, &calls) == 1 && calls == 1);
    for (n = 1; n <= 8; ++n) {
        mode = n;
        assert(wr_band_receive(42, buffer, sizeof(buffer), &route, 1, event, &calls) == -1);
        assert(calls == 1);
        if (n == 1) assert(errno == EAGAIN);
        else if (n == 2) assert(errno == ENOBUFS);
        else if (n == 3 || n == 7) assert(errno == EMSGSIZE);
        else assert(errno == EPROTO);
    }
    assert(wr_band_receive(-1, buffer, sizeof(buffer), &route, 1, event, &calls) == -1 && errno == EBADF);
    assert(wr_band_receive(42, buffer, 0, &route, 1, event, &calls) == -1 && errno == EINVAL);
    puts("PASS: nonblocking listener, kernel sender, truncation and cleanup; all syscalls mocked");
    return 0;
}
