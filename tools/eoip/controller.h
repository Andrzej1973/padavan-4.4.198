#ifndef WR_EOIP_CONTROLLER_H
#define WR_EOIP_CONTROLLER_H
/* Managed-service controller: maps one slot to its fixed managed interface
 * name and ownership alias and implements the lifecycle operations against the
 * kernel.
 *
 * The netlink transport is injected, so the same controller code runs behind a
 * test transport and, in firmware, behind the daemon's own socket. Every
 * mutation is preceded by a fresh observation and followed by the caller's own
 * post-state check; nothing is adopted, detached or deleted without a verified
 * ownership identity. This is not a service manager: table persistence, boot
 * policy and the WebUI remain separate work. */
#include "configure.h"
#include "lifecycle.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Private attributes of the pinned eoip module, mirrored by observation.h:
 * IFLA_EOIP_KA_INTERVAL (u32) and IFLA_EOIP_KA_RETRIES (u8). */
#define WR_EOIP_KA_INTERVAL_ATTR 32
#define WR_EOIP_KA_RETRIES_ATTR 33
#define WR_EOIP_REQUEST_LENGTH 256
#define WR_EOIP_TTL 64
#define WR_EOIP_TOS 0
#define WR_EOIP_SEQUENCE_CREATE 0x57454f31U
#define WR_EOIP_SEQUENCE_DELETE 0x57454f33U

struct wr_eoip_transport {
    void *context;
    /* Sends one bounded request; returns 0 only when the kernel acknowledged
     * it with a zero error. The implementation owns its socket. */
    int (*talk)(void *context, const void *request, size_t length, uint32_t sequence);
    /* Read-only observation of one interface, following netlink-query.h. */
    int (*query)(void *context, const char *name, const char *owner,
                 struct wr_eoip_observation *out);
};

/* The managed interface name and alias are fixed per slot so that a stale
 * record can never point at another interface. */
static inline int wr_eoip_slot_name(unsigned slot, char *out, size_t size)
{
    if (slot >= WR_EOIP_SLOTS || !out || size < 11) return 0;
    snprintf(out, size, "wr-eoip%u", slot);
    return 1;
}

static inline int wr_eoip_slot_owner(unsigned slot, char *out, size_t size)
{
    if (slot >= WR_EOIP_SLOTS || !out || size < 16) return 0;
    snprintf(out, size, "wr-eoip:%u:v1", slot);
    return 1;
}

/* Bounded attribute writer for requests built in caller-provided storage. */
static inline int wr_eoip_request_attr(unsigned char *request, size_t capacity, size_t *offset,
                                       unsigned type, const void *data, size_t size)
{
    struct rtattr *attribute;
    size_t length, aligned;

    if (!request || !offset) return 0;
    length = RTA_LENGTH(size);
    aligned = RTA_ALIGN(length);
    if (*offset > capacity || aligned > capacity - *offset) return 0;
    attribute = (struct rtattr *)(request + *offset);
    attribute->rta_type = (unsigned short)type;
    attribute->rta_len = (unsigned short)length;
    if (size) memcpy(request + *offset + RTA_LENGTH(0), data, size);
    *offset += aligned;
    return 1;
}

static inline int wr_eoip_request_attr_u32(unsigned char *request, size_t capacity, size_t *offset,
                                           unsigned type, uint32_t value)
{
    return wr_eoip_request_attr(request, capacity, offset, type, &value, sizeof(value));
}

static inline int wr_eoip_request_attr_u8(unsigned char *request, size_t capacity, size_t *offset,
                                          unsigned type, unsigned char value)
{
    return wr_eoip_request_attr(request, capacity, offset, type, &value, sizeof(value));
}

/* Exclusive create of one managed IPv4 EoIP link. The name, the ownership
 * alias, the kind and every tunnel parameter travel in the same request, so no
 * window exists in which an unowned interface carries the managed name. */
static inline int wr_eoip_build_owned_create(unsigned char *request, size_t capacity,
                                             const struct wr_eoip_config *config,
                                             uint32_t sequence, size_t *length)
{
    struct nlmsghdr header;
    struct ifinfomsg info;
    char name[16], owner[16];
    size_t offset, linkinfo, data;

    if (!request || !length || !config) return 0;
    if (config->slot >= WR_EOIP_SLOTS || config->enabled != 1) return 0;
    if (config->mtu < 68 || config->mtu > WR_EOIP_MAX_MTU) return 0;
    if (config->keepalive > 3600 || config->retries > 255) return 0;
    if (!wr_eoip_slot_name(config->slot, name, sizeof(name))) return 0;
    if (!wr_eoip_slot_owner(config->slot, owner, sizeof(owner))) return 0;

    offset = NLMSG_LENGTH(sizeof(info));
    if (offset > capacity) return 0;
    memset(request, 0, capacity);
    memset(&header, 0, sizeof(header));
    memset(&info, 0, sizeof(info));
    info.ifi_family = AF_UNSPEC;

    if (!wr_eoip_request_attr(request, capacity, &offset, IFLA_IFNAME, name, strlen(name) + 1)) return 0;
    if (!wr_eoip_request_attr(request, capacity, &offset, IFLA_IFALIAS, owner, strlen(owner) + 1)) return 0;
    linkinfo = offset;
    if (!wr_eoip_request_attr(request, capacity, &offset, IFLA_LINKINFO, NULL, 0)) return 0;
    if (!wr_eoip_request_attr(request, capacity, &offset, IFLA_INFO_KIND, "eoip", 5)) return 0;
    data = offset;
    if (!wr_eoip_request_attr(request, capacity, &offset, IFLA_INFO_DATA, NULL, 0)) return 0;
    if (!wr_eoip_request_attr_u32(request, capacity, &offset, IFLA_GRE_IKEY, config->tunnel_id)) return 0;
    if (!wr_eoip_request_attr(request, capacity, &offset, IFLA_GRE_LOCAL,
                              &config->local.s_addr, sizeof(config->local.s_addr))) return 0;
    if (!wr_eoip_request_attr(request, capacity, &offset, IFLA_GRE_REMOTE,
                              &config->remote.s_addr, sizeof(config->remote.s_addr))) return 0;
    if (!wr_eoip_request_attr_u32(request, capacity, &offset, IFLA_GRE_LINK, 0)) return 0;
    if (!wr_eoip_request_attr_u8(request, capacity, &offset, IFLA_GRE_TTL, WR_EOIP_TTL)) return 0;
    if (!wr_eoip_request_attr_u8(request, capacity, &offset, IFLA_GRE_TOS, WR_EOIP_TOS)) return 0;
    if (!wr_eoip_request_attr_u32(request, capacity, &offset, WR_EOIP_KA_INTERVAL_ATTR,
                                  config->keepalive)) return 0;
    if (!wr_eoip_request_attr_u8(request, capacity, &offset, WR_EOIP_KA_RETRIES_ATTR,
                                 (unsigned char)config->retries)) return 0;
    ((struct rtattr *)(request + data))->rta_len = (unsigned short)(offset - data);
    ((struct rtattr *)(request + linkinfo))->rta_len = (unsigned short)(offset - linkinfo);

    header.nlmsg_len = (unsigned)offset;
    header.nlmsg_type = RTM_NEWLINK;
    header.nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_EXCL;
    header.nlmsg_seq = sequence;
    memcpy(request, &header, sizeof(header));
    memcpy(request + NLMSG_HDRLEN, &info, sizeof(info));
    *length = offset;
    return 1;
}

/* Deletion addresses exactly one observed interface index. */
static inline int wr_eoip_build_owned_delete(unsigned char *request, size_t capacity, unsigned index,
                                             uint32_t sequence, size_t *length)
{
    struct nlmsghdr header;
    struct ifinfomsg info;
    size_t size = NLMSG_LENGTH(sizeof(info));

    if (!request || !length || !index || index > 0x7fffffffU) return 0;
    if (size > capacity) return 0;
    memset(request, 0, capacity);
    memset(&header, 0, sizeof(header));
    memset(&info, 0, sizeof(info));
    info.ifi_family = AF_UNSPEC;
    info.ifi_index = (int)index;
    header.nlmsg_len = (unsigned)size;
    header.nlmsg_type = RTM_DELLINK;
    header.nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
    header.nlmsg_seq = sequence;
    memcpy(request, &header, sizeof(header));
    memcpy(request + NLMSG_HDRLEN, &info, sizeof(info));
    *length = size;
    return 1;
}

/* 1 only for a zero-error acknowledgement of the echoed request type. */
static inline int wr_eoip_ack_ok(const void *buffer, size_t size, const struct sockaddr_nl *sender,
                                 socklen_t sender_length, int flags, uint32_t sequence,
                                 unsigned expected_type)
{
    struct nlmsghdr header;
    struct nlmsgerr error;

    if (!buffer || !sender || sender_length != sizeof(*sender) || sender->nl_family != AF_NETLINK) return 0;
    if (sender->nl_pid != 0 || sender->nl_groups != 0 || (flags & (MSG_TRUNC | MSG_CTRUNC))) return 0;
    if (size < sizeof(header) || size > 4096) return 0;
    memcpy(&header, buffer, sizeof(header));
    if (header.nlmsg_len != size || header.nlmsg_seq != sequence || header.nlmsg_type != NLMSG_ERROR) return 0;
    if (size < NLMSG_LENGTH(sizeof(error))) return 0;
    memcpy(&error, (const unsigned char *)buffer + NLMSG_HDRLEN, sizeof(error));
    if (error.error) return 0;
    return error.msg.nlmsg_type == expected_type && error.msg.nlmsg_seq == sequence;
}

/* One socket transport serves create, change and delete: the acknowledged
 * message type is read back from the request that is being sent. */
static inline int wr_eoip_socket_talk(void *context, const void *request, size_t length, uint32_t sequence)
{
    unsigned char reply[4096];
    struct sockaddr_nl local, kernel, sender;
    struct timeval timeout;
    struct iovec vector;
    struct msghdr message;
    struct nlmsghdr header;
    int descriptor, result = -1;
    ssize_t received;

    (void)context;
    if (!request || length < NLMSG_HDRLEN || length > WR_EOIP_REQUEST_LENGTH) return -1;
    memcpy(&header, request, sizeof(header));
    if (header.nlmsg_type != RTM_NEWLINK && header.nlmsg_type != RTM_DELLINK) return -1;
    descriptor = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (descriptor < 0) return -1;
    memset(&local, 0, sizeof(local));
    local.nl_family = AF_NETLINK;
    memset(&kernel, 0, sizeof(kernel));
    kernel.nl_family = AF_NETLINK;
    timeout.tv_sec = 1;
    timeout.tv_usec = 0;
    if (fcntl(descriptor, F_SETFD, FD_CLOEXEC) < 0 ||
        setsockopt(descriptor, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) ||
        setsockopt(descriptor, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)) ||
        bind(descriptor, (struct sockaddr *)&local, sizeof(local)) ||
        sendto(descriptor, request, length, 0, (struct sockaddr *)&kernel, sizeof(kernel)) != (ssize_t)length)
        goto done;
    memset(&sender, 0, sizeof(sender));
    memset(&message, 0, sizeof(message));
    vector.iov_base = reply;
    vector.iov_len = sizeof(reply);
    message.msg_name = &sender;
    message.msg_namelen = sizeof(sender);
    message.msg_iov = &vector;
    message.msg_iovlen = 1;
    received = recvmsg(descriptor, &message, 0);
    if (received > 0 && wr_eoip_ack_ok(reply, (size_t)received, &sender, message.msg_namelen,
                                      message.msg_flags, sequence, header.nlmsg_type))
        result = 0;
done:
    close(descriptor);
    return result;
}

static inline int wr_eoip_controller_query(void *context, unsigned slot,
                                           struct wr_eoip_observation *out)
{
    const struct wr_eoip_transport *transport = context;
    char name[16], owner[16];

    if (!transport || !transport->query || !out) return 0;
    if (!wr_eoip_slot_name(slot, name, sizeof(name))) return 0;
    if (!wr_eoip_slot_owner(slot, owner, sizeof(owner))) return 0;
    return transport->query(transport->context, name, owner, out);
}

static inline int wr_eoip_controller_create(void *context, const struct wr_eoip_config *config)
{
    const struct wr_eoip_transport *transport = context;
    unsigned char request[WR_EOIP_REQUEST_LENGTH];
    size_t length = 0;

    if (!transport || !transport->talk || !config) return 1;
    if (!wr_eoip_build_owned_create(request, sizeof(request), config, WR_EOIP_SEQUENCE_CREATE, &length)) return 1;
    return transport->talk(transport->context, request, length, WR_EOIP_SEQUENCE_CREATE) ? 1 : 0;
}

static inline int wr_eoip_controller_configure(void *context, const struct wr_eoip_config *config,
                                               unsigned index, unsigned *master)
{
    const struct wr_eoip_transport *transport = context;
    char name[16], owner[16];

    if (!master) return 1;
    *master = 0;
    if (!transport || !transport->talk || !transport->query || !config) return 1;
    if (!wr_eoip_slot_name(config->slot, name, sizeof(name))) return 1;
    if (!wr_eoip_slot_owner(config->slot, owner, sizeof(owner))) return 1;
    return wr_eoip_configure(transport->talk, transport->context, transport->query, transport->context,
                             name, owner, index, config->mtu, config->bridge, master) ? 0 : 1;
}

/* Cleanup deliberately needs no endpoint or MTU validation: a saved profile
 * that is invalid must still be removable. */
static inline int wr_eoip_controller_remove(void *context, unsigned slot, unsigned index)
{
    const struct wr_eoip_transport *transport = context;
    struct wr_eoip_observation observed;
    unsigned char request[WR_EOIP_REQUEST_LENGTH];
    char name[16], owner[16];
    size_t length = 0;
    int present;

    if (!transport || !transport->talk || !transport->query || !index) return 1;
    if (!wr_eoip_slot_name(slot, name, sizeof(name))) return 1;
    if (!wr_eoip_slot_owner(slot, owner, sizeof(owner))) return 1;
    present = transport->query(transport->context, name, owner, &observed);
    if (present == 1) return 0;
    if (present != 2 || !observed.owned || observed.ifindex != (int)index) return 1;
    if (!wr_eoip_build_owned_delete(request, sizeof(request), index, WR_EOIP_SEQUENCE_DELETE, &length)) return 1;
    if (transport->talk(transport->context, request, length, WR_EOIP_SEQUENCE_DELETE)) return 1;
    return transport->query(transport->context, name, owner, &observed) == 1 ? 0 : 1;
}

static inline void wr_eoip_controller_ops(struct wr_eoip_ops *ops, struct wr_eoip_transport *transport)
{
    if (!ops) return;
    ops->context = transport;
    ops->query = wr_eoip_controller_query;
    ops->create = wr_eoip_controller_create;
    ops->configure = wr_eoip_controller_configure;
    ops->remove = wr_eoip_controller_remove;
}
#endif