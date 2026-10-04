#include "listener.h"
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
int wr_band_listener_open(void)
{
    struct sockaddr_nl address;
    int fd, saved, receive_size = 262144;
    fd = socket(AF_NETLINK, SOCK_RAW | SOCK_NONBLOCK | SOCK_CLOEXEC, NETLINK_ROUTE);
    if (fd < 0) return -1;
    memset(&address, 0, sizeof(address));
    address.nl_family = AF_NETLINK;
    address.nl_groups = RTMGRP_LINK;
    if (setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &receive_size, sizeof(receive_size)) < 0 ||
        bind(fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        saved = errno; close(fd); errno = saved; return -1;
    }
    return fd;
}
int wr_band_receive(int fd, uint8_t *buffer, size_t capacity,
    const struct wr_band_route *routes, size_t count,
    wr_band_event_callback callback, void *context)
{
    struct sockaddr_nl sender;
    struct iovec vector;
    struct msghdr message;
    ssize_t bytes;
    int events;
    if (fd < 0) { errno = EBADF; return -1; }
    if (!buffer || !capacity || capacity > 65536 || !routes || !count || count > 2) {
        errno = EINVAL; return -1;
    }
    memset(&sender, 0, sizeof(sender));
    memset(&message, 0, sizeof(message));
    vector.iov_base = buffer; vector.iov_len = capacity;
    message.msg_name = &sender; message.msg_namelen = sizeof(sender);
    message.msg_iov = &vector; message.msg_iovlen = 1;
    bytes = recvmsg(fd, &message, 0);
    if (bytes < 0) return -1;
    if ((message.msg_flags & (MSG_TRUNC | MSG_CTRUNC)) || (size_t)bytes > capacity) {
        errno = EMSGSIZE; return -1;
    }
    if (!bytes || message.msg_namelen != sizeof(sender) ||
        sender.nl_family != AF_NETLINK || sender.nl_pid != 0) {
        errno = EPROTO; return -1;
    }
    events = wr_band_parse_netlink(buffer, (size_t)bytes, routes, count, callback, context);
    if (events < 0) errno = EPROTO;
    return events;
}
