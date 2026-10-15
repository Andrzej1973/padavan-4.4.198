#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#define WR_EOIP_WORKER_NO_MAIN
#include "worker.c"

struct fake_link {
    const char *name;
    const char *alias;
    const char *kind;
    int index;
    unsigned flags, mtu, master, present;
    uint32_t local, remote, tunnel_id, keepalive;
    unsigned retries;
};
static struct fake_link links[2];
static int create_calls, delete_calls, query_unknown;
static unsigned last_delete_index;

static struct fake_link *find_link(const char *name)
{
    int i;
    for (i = 0; i < 2; i++) {
        if (links[i].name && !strcmp(links[i].name, name)) return &links[i];
    }
    return NULL;
}

static int mock_query(void *context, const char *name, const char *owner,
                      struct wr_eoip_observation *out)
{
    struct fake_link *link = find_link(name);

    (void)context;
    memset(out, 0, sizeof(*out));
    if (query_unknown) return 0;
    if (!link || !link->present) return 1;
    out->ifindex = link->index;
    out->flags = link->flags;
    out->mtu = link->mtu;
    out->master = link->master;
    snprintf(out->name, sizeof(out->name), "%s", link->name);
    snprintf(out->kind, sizeof(out->kind), "%s", link->kind ? link->kind : "eoip");
    if (link->alias) snprintf(out->alias, sizeof(out->alias), "%s", link->alias);
    out->owned = link->alias && !strcmp(link->alias, owner);
    out->parameters = 31;
    out->local = link->local;
    out->remote = link->remote;
    out->tunnel_id = link->tunnel_id;
    out->keepalive = link->keepalive;
    out->retries = link->retries;
    return 2;
}

static const struct rtattr *attr_find(const unsigned char *base, size_t length, unsigned type)
{
    size_t offset = 0;
    while (offset + sizeof(struct rtattr) <= length) {
        const struct rtattr *attribute = (const struct rtattr *)(base + offset);
        size_t aligned;
        if (attribute->rta_len < RTA_LENGTH(0) || attribute->rta_len > length - offset) return NULL;
        if ((attribute->rta_type & 0x3fff) == type) return attribute;
        aligned = RTA_ALIGN(attribute->rta_len);
        if (aligned > length - offset) return NULL;
        offset += aligned;
    }
    return NULL;
}

static unsigned attr_u32(const struct rtattr *attribute)
{
    unsigned value = 0;
    assert(attribute && attribute->rta_len == RTA_LENGTH(sizeof(uint32_t)));
    memcpy(&value, (const unsigned char *)attribute + RTA_LENGTH(0), sizeof(value));
    return value;
}

static int mock_talk(void *context, const void *request, size_t length, uint32_t sequence)
{
    const unsigned char *bytes = request;
    const struct rtattr *attribute, *linkinfo, *kind, *data;
    const struct rtattr *local_attr, *remote_attr, *keepalive_attr, *retries_attr;
    const unsigned char *payload, *children;
    struct nlmsghdr header;
    struct ifinfomsg info;
    size_t payload_length, children_length;

    (void)context;
    (void)sequence;
    memcpy(&header, request, sizeof(header));
    memcpy(&info, bytes + NLMSG_HDRLEN, sizeof(info));
    payload = bytes + NLMSG_LENGTH(sizeof(info));
    payload_length = length - NLMSG_LENGTH(sizeof(info));
    if (header.nlmsg_type == RTM_DELLINK) {
        delete_calls++;
        last_delete_index = (unsigned)info.ifi_index;
        links[0].present = 0;
        return 0;
    }
    assert(header.nlmsg_type == RTM_NEWLINK);
    if (header.nlmsg_flags & NLM_F_CREATE) {
        create_calls++;
        attribute = attr_find(payload, payload_length, IFLA_IFNAME);
        assert(attribute && !strcmp((const char *)attribute + RTA_LENGTH(0), "wr-eoip0"));
        linkinfo = attr_find(payload, payload_length, IFLA_LINKINFO);
        assert(linkinfo);
        children = (const unsigned char *)linkinfo + RTA_LENGTH(0);
        children_length = linkinfo->rta_len - RTA_LENGTH(0);
        kind = attr_find(children, children_length, IFLA_INFO_KIND);
        assert(kind && !strcmp((const char *)kind + RTA_LENGTH(0), "eoip"));
        data = attr_find(children, children_length, IFLA_INFO_DATA);
        assert(data);
        children = (const unsigned char *)data + RTA_LENGTH(0);
        children_length = data->rta_len - RTA_LENGTH(0);
        local_attr = attr_find(children, children_length, IFLA_GRE_LOCAL);
        remote_attr = attr_find(children, children_length, IFLA_GRE_REMOTE);
        keepalive_attr = attr_find(children, children_length, WR_EOIP_KA_INTERVAL_ATTR);
        retries_attr = attr_find(children, children_length, WR_EOIP_KA_RETRIES_ATTR);
        assert(local_attr && remote_attr && keepalive_attr && retries_attr);
        links[0].present = 1;
        links[0].index = 42;
        links[0].flags = 0;
        links[0].tunnel_id = attr_u32(attr_find(children, children_length, IFLA_GRE_IKEY));
        memcpy(&links[0].local, (const unsigned char *)local_attr + RTA_LENGTH(0), 4);
        memcpy(&links[0].remote, (const unsigned char *)remote_attr + RTA_LENGTH(0), 4);
        links[0].keepalive = attr_u32(keepalive_attr);
        links[0].retries = 0;
        memcpy(&links[0].retries, (const unsigned char *)retries_attr + RTA_LENGTH(0), 1);
        return 0;
    }
    attribute = attr_find(payload, payload_length, IFLA_MTU);
    assert(attribute);
    links[0].mtu = attr_u32(attribute);
    attribute = attr_find(payload, payload_length, IFLA_MASTER);
    links[0].master = attribute ? attr_u32(attribute) : 0;
    links[0].flags |= 1U;
    return 0;
}

int main(void)
{
    char directory[] = "/tmp/wr-eoip-work-XXXXXX", message[WR_EOIP_WORKER_MESSAGE], path[PATH_MAX];
    struct wr_eoip_transport transport = { .context = NULL, .talk = mock_talk, .query = mock_query };
    struct wr_eoip_worker worker;
    char *short_argv[] = { "eoip-service" };
    char *unknown_argv[] = { "eoip-service", "restart", "0" };
    char *short_start[] = { "eoip-service", "start", "0", "1", "0", "0.0.0.0", "10.0.0.2", "7", "1458", "30" };
    char *bad_mtu[] = { "eoip-service", "start", "0", "1", "0", "0.0.0.0", "10.0.0.2", "7", "67", "30", "3", "br0" };
    char *bad_remote[] = { "eoip-service", "start", "0", "1", "0", "0.0.0.0", "0.0.0.0", "7", "1458", "30", "3", "br0" };
    char *bad_bridge[] = { "eoip-service", "start", "0", "1", "0", "0.0.0.0", "10.0.0.2", "7", "1458", "30", "3", "br 0" };
    char *start[] = { "eoip-service", "start", "0", "1", "0", "0.0.0.0", "10.0.0.2", "7", "1458", "30", "3", "br0" };
    char *disable[] = { "eoip-service", "start", "0", "0", "0", "0.0.0.0", "10.0.0.2", "7", "1458", "30", "3", "br0" };
    char *status[] = { "eoip-service", "status", "0" };
    char *stop[] = { "eoip-service", "stop", "0" };
    char *bad_slot[] = { "eoip-service", "stop", "9" };

    assert(mkdtemp(directory));
    worker.transport = &transport;
    worker.directory = directory;
    links[0] = (struct fake_link){ "wr-eoip0", "wr-eoip:0:v1", "eoip", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
    links[1] = (struct fake_link){ "br0", NULL, "bridge", 9, 1U, 1500, 0, 1, 0, 0, 0, 0, 0 };

    /* Argument handling. */
    assert(wr_eoip_worker_dispatch(&worker, 1, short_argv, message, sizeof(message)) == WR_EOIP_WORKER_USAGE);
    assert(strstr(message, "usage"));
    assert(wr_eoip_worker_dispatch(&worker, 3, unknown_argv, message, sizeof(message)) == WR_EOIP_WORKER_USAGE);
    assert(wr_eoip_worker_dispatch(&worker, 10, short_start, message, sizeof(message)) == WR_EOIP_WORKER_USAGE);
    assert(wr_eoip_worker_dispatch(&worker, 3, bad_slot, message, sizeof(message)) == WR_EOIP_WORKER_USAGE);
    assert(wr_eoip_worker_dispatch(NULL, 3, status, message, sizeof(message)) == WR_EOIP_WORKER_USAGE);
    assert(wr_eoip_worker_dispatch(&worker, 3, status, NULL, 0) == WR_EOIP_WORKER_USAGE);
    worker.transport = NULL;
    assert(wr_eoip_worker_dispatch(&worker, 3, status, message, sizeof(message)) == WR_EOIP_WORKER_USAGE);
    worker.transport = &transport;

    /* A profile that the validator rejects never reaches the kernel. */
    assert(wr_eoip_worker_dispatch(&worker, 12, bad_mtu, message, sizeof(message)) == WR_EOIP_WORKER_INVALID);
    assert(strstr(message, "profile invalid"));
    assert(wr_eoip_worker_dispatch(&worker, 12, bad_remote, message, sizeof(message)) == WR_EOIP_WORKER_INVALID);
    assert(wr_eoip_worker_dispatch(&worker, 12, bad_bridge, message, sizeof(message)) == WR_EOIP_WORKER_INVALID);
    assert(create_calls == 0);

    /* Validate the whole table before the first mutation. Disabled slots may
     * contain empty endpoints; enabled duplicate tuples must refuse. */
    {
        char *table[82] = {"eoip-service", "boot-table"};
        char slots[8][2];
        unsigned n, field;
        for (n = 0; n < 8; n++) {
            slots[n][0] = (char)('0' + n);
            slots[n][1] = 0;
            for (field = 0; field < 10; field++) table[2 + n * 10 + field] = "";
            table[2 + n * 10] = slots[n];
            table[3 + n * 10] = "0";
            table[4 + n * 10] = "0";
        }
        assert(wr_eoip_worker_dispatch(&worker, 82, table, message, sizeof(message)) == WR_EOIP_WORKER_OK);
        for (n = 0; n < 2; n++) {
            for (field = 1; field < 10; field++) table[2 + n * 10 + field] = start[2 + field];
            table[4 + n * 10] = "1";
        }
        assert(wr_eoip_worker_dispatch(&worker, 82, table, message, sizeof(message)) == WR_EOIP_WORKER_INVALID);
        assert(strstr(message, "conflicts") && create_calls == 0);
    }

    /* A slot that does not exist is reported as absent, not as an error. */
    assert(wr_eoip_worker_dispatch(&worker, 3, status, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(strstr(message, "absent"));

    /* Full start: create, observe, record, configure and verify. */
    assert(wr_eoip_worker_dispatch(&worker, 12, start, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(strstr(message, "started index 42"));
    assert(create_calls == 1 && links[0].present == 1 && links[0].index == 42);
    assert(links[0].mtu == 1458 && links[0].master == 9 && (links[0].flags & 1U));
    assert(wr_eoip_worker_dispatch(&worker, 3, status, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(strstr(message, "owned index 42") && strstr(message, "mtu 1458"));

    /* An existing managed interface is refused, not replaced. */
    assert(wr_eoip_worker_dispatch(&worker, 12, start, message, sizeof(message)) == WR_EOIP_WORKER_REFUSED);
    assert(strstr(message, "refused") && create_calls == 1);

    /* Disabling the profile removes the interface through the same path. */
    disable[5] = "broken endpoint";
    disable[8] = "broken mtu";
    assert(wr_eoip_worker_dispatch(&worker, 12, disable, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(strstr(message, "stopped"));
    assert(delete_calls == 1 && last_delete_index == 42 && links[0].present == 0);
    assert(wr_eoip_worker_dispatch(&worker, 3, stop, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(wr_eoip_worker_dispatch(&worker, 3, status, message, sizeof(message)) == WR_EOIP_WORKER_OK);
    assert(strstr(message, "absent"));

    /* An unknown observation is unconfirmed, never success. */
    query_unknown = 1;
    assert(wr_eoip_worker_dispatch(&worker, 3, status, message, sizeof(message)) == WR_EOIP_WORKER_UNCONFIRMED);
    assert(strstr(message, "unknown"));
    assert(wr_eoip_worker_dispatch(&worker, 3, stop, message, sizeof(message)) == WR_EOIP_WORKER_REFUSED);
    query_unknown = 0;

    /* A foreign interface holding the managed name is never adopted or removed. */
    links[0].present = 1;
    links[0].kind = "veth";
    links[0].alias = NULL;
    assert(wr_eoip_worker_dispatch(&worker, 3, status, message, sizeof(message)) == WR_EOIP_WORKER_REFUSED);
    assert(strstr(message, "foreign"));
    assert(wr_eoip_worker_dispatch(&worker, 12, start, message, sizeof(message)) == WR_EOIP_WORKER_REFUSED);
    assert(create_calls == 1 && delete_calls == 1 && links[0].present == 1);

    {
        struct wr_eoip_state held = {.fd = -1};
        assert(wr_eoip_state_lock_named(directory, &held, "operation-lock"));
        assert(wr_eoip_worker_dispatch(&worker, 12, start, message, sizeof(message)) == WR_EOIP_WORKER_REFUSED);
        assert(strstr(message, "operation busy"));
        assert(create_calls == 1 && delete_calls == 1);
        wr_eoip_state_unlock(&held);
    }
    snprintf(path, sizeof(path), "%s/lock", directory);
    unlink(path);
    snprintf(path, sizeof(path), "%s/operation-lock", directory);
    unlink(path);
    assert(rmdir(directory) == 0);
    puts("PASS EoIP worker: usage, profile validation, start, status, disable cleanup, foreign and unknown refusal");
    return 0;
}
