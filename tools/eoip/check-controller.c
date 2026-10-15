#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "controller.h"

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
static int talk_calls, create_calls, delete_calls;
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
    const unsigned char *payload, *children;
    struct nlmsghdr header;
    struct ifinfomsg info;
    size_t payload_length, children_length;
    uint32_t mtu = 0, master = 0;

    (void)context;
    talk_calls++;
    assert(length == ((const struct nlmsghdr *)request)->nlmsg_len);
    memcpy(&header, request, sizeof(header));
    memcpy(&info, bytes + NLMSG_HDRLEN, sizeof(info));
    assert(header.nlmsg_flags & NLM_F_REQUEST);
    assert(header.nlmsg_flags & NLM_F_ACK);
    assert(header.nlmsg_seq == sequence);
    payload = bytes + NLMSG_LENGTH(sizeof(info));
    payload_length = length - NLMSG_LENGTH(sizeof(info));

    if (header.nlmsg_type == RTM_DELLINK) {
        delete_calls++;
        last_delete_index = (unsigned)info.ifi_index;
        assert(info.ifi_family == AF_UNSPEC);
        links[0].present = 0;
        return 0;
    }
    assert(header.nlmsg_type == RTM_NEWLINK);
    if (header.nlmsg_flags & NLM_F_CREATE) {
        const struct rtattr *local_attr, *remote_attr, *key_attr, *ka_attr, *retry_attr;
        create_calls++;
        assert(header.nlmsg_flags & NLM_F_EXCL);
        assert(header.nlmsg_seq == WR_EOIP_SEQUENCE_CREATE);
        attribute = attr_find(payload, payload_length, IFLA_IFNAME);
        assert(attribute && !strcmp((const char *)attribute + RTA_LENGTH(0), "wr-eoip0"));
        attribute = attr_find(payload, payload_length, IFLA_IFALIAS);
        assert(attribute && !strcmp((const char *)attribute + RTA_LENGTH(0), "wr-eoip:0:v1"));
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
        key_attr = attr_find(children, children_length, IFLA_GRE_IKEY);
        local_attr = attr_find(children, children_length, IFLA_GRE_LOCAL);
        remote_attr = attr_find(children, children_length, IFLA_GRE_REMOTE);
        ka_attr = attr_find(children, children_length, WR_EOIP_KA_INTERVAL_ATTR);
        retry_attr = attr_find(children, children_length, WR_EOIP_KA_RETRIES_ATTR);
        assert(key_attr && local_attr && remote_attr && ka_attr && retry_attr);
        links[0].present = 1;
        links[0].index = 42;
        links[0].flags = 0;
        links[0].tunnel_id = attr_u32(key_attr);
        memcpy(&links[0].local, (const unsigned char *)local_attr + RTA_LENGTH(0), 4);
        memcpy(&links[0].remote, (const unsigned char *)remote_attr + RTA_LENGTH(0), 4);
        links[0].keepalive = attr_u32(ka_attr);
        memcpy(&links[0].retries, (const unsigned char *)retry_attr + RTA_LENGTH(0), 1);
        return 0;
    }
    attribute = attr_find(payload, payload_length, IFLA_MTU);
    assert(attribute);
    mtu = attr_u32(attribute);
    attribute = attr_find(payload, payload_length, IFLA_MASTER);
    if (attribute) master = attr_u32(attribute);
    links[0].mtu = mtu;
    links[0].master = master;
    links[0].flags |= 1U;
    return 0;
}

static int record_read(const char *directory, unsigned *index)
{
    struct wr_eoip_state state = { .fd = -1 };
    int result;
    assert(wr_eoip_state_lock(directory, &state));
    result = wr_eoip_state_read(&state, 0, index);
    wr_eoip_state_unlock(&state);
    return result;
}

int main(void)
{
    char directory[] = "/tmp/wr-eoip-ctl-XXXXXX", path[PATH_MAX], name[16], owner[16];
    unsigned char request[WR_EOIP_REQUEST_LENGTH];
    struct wr_eoip_config config;
    struct wr_eoip_transport transport;
    struct wr_eoip_ops ops;
    struct wr_eoip_observation observation;
    unsigned master = 77, index = 0, sequence = 0x11111111U;
    size_t length = 0;

    /* Slot mapping is fixed and bounded. */
    assert(wr_eoip_slot_name(0, name, sizeof(name)) && !strcmp(name, "wr-eoip0"));
    assert(wr_eoip_slot_name(7, name, sizeof(name)) && !strcmp(name, "wr-eoip7"));
    assert(wr_eoip_slot_owner(7, owner, sizeof(owner)) && !strcmp(owner, "wr-eoip:7:v1"));
    assert(!wr_eoip_slot_name(WR_EOIP_SLOTS, name, sizeof(name)));
    assert(!wr_eoip_slot_owner(WR_EOIP_SLOTS, owner, sizeof(owner)));
    assert(!wr_eoip_slot_name(0, name, 4));
    assert(!wr_eoip_slot_owner(0, owner, 4));

    /* The create request carries name, alias, kind and every parameter. */
    assert(wr_eoip_validate("0", "1", "0", "0.0.0.0", "10.0.0.2", "7", "1458", "30", "3", "br0", &config));
    assert(wr_eoip_build_owned_create(request, sizeof(request), &config, WR_EOIP_SEQUENCE_CREATE, &length));
    assert(length > NLMSG_LENGTH(sizeof(struct ifinfomsg)));
    assert(!wr_eoip_build_owned_create(request, 24, &config, 1, &length));
    assert(!wr_eoip_build_owned_create(request, sizeof(request), &config, 1, NULL));
    assert(!wr_eoip_build_owned_create(NULL, sizeof(request), &config, 1, &length));
    assert(!wr_eoip_build_owned_delete(request, sizeof(request), 0, 1, &length));
    assert(wr_eoip_build_owned_delete(request, sizeof(request), 42, WR_EOIP_SEQUENCE_DELETE, &length));
    assert(sequence != WR_EOIP_SEQUENCE_DELETE);

    /* A foreign interface holding the managed name is never adopted. */
    links[0] = (struct fake_link){ "wr-eoip0", "wr-eoip:0:v1", "veth", 5, 1U, 1500, 0, 1, 0, 0, 0, 0, 0 };
    links[1] = (struct fake_link){ "br0", NULL, "bridge", 9, 1U, 1500, 0, 1, 0, 0, 0, 0, 0 };
    transport = (struct wr_eoip_transport){ .context = NULL, .talk = mock_talk, .query = mock_query };
    wr_eoip_controller_ops(&ops, &transport);
    assert(mkdtemp(directory));
    assert(wr_eoip_lifecycle_start(directory, &config, &ops) == WR_EOIP_REFUSED);
    assert(create_calls == 0 && delete_calls == 0);

    /* Full path: create, observe, record, configure, verify. */
    links[0].present = 0;
    assert(wr_eoip_lifecycle_start(directory, &config, &ops) == WR_EOIP_OK);
    assert(create_calls == 1 && talk_calls == 2);
    assert(links[0].present == 1 && links[0].index == 42);
    assert(links[0].tunnel_id == config.tunnel_id);
    assert(links[0].local == config.local.s_addr && links[0].remote == config.remote.s_addr);
    assert(links[0].keepalive == config.keepalive && links[0].retries == config.retries);
    assert(links[0].mtu == config.mtu && links[0].master == 9 && (links[0].flags & 1U));
    assert(record_read(directory, &index) == 2 && index == 42);
    assert(wr_eoip_lifecycle_start(directory, &config, &ops) == WR_EOIP_REFUSED && create_calls == 1);

    /* An index that no longer matches the record stops cleanup. */
    links[0].index = 43;
    assert(wr_eoip_lifecycle_stop(directory, 0, &ops) == WR_EOIP_REFUSED && delete_calls == 0);
    links[0].index = 42;
    assert(wr_eoip_lifecycle_stop(directory, 0, &ops) == WR_EOIP_OK);
    assert(delete_calls == 1 && last_delete_index == 42 && links[0].present == 0);
    assert(record_read(directory, &index) == 1);
    assert(wr_eoip_lifecycle_stop(directory, 0, &ops) == WR_EOIP_OK);

    /* A name that now belongs to another interface is refused. */
    links[0].present = 1;
    links[0].kind = "veth";
    links[0].alias = NULL;
    assert(wr_eoip_controller_query(&transport, 0, &observation) == 2);
    assert(observation.owned == 0);
    assert(wr_eoip_controller_remove(&transport, 0, 42) == 1);
    assert(wr_eoip_controller_remove(&transport, WR_EOIP_SLOTS, 42) == 1);
    assert(links[0].present == 1);

    /* Without a transport or a master output the controller refuses. */
    assert(wr_eoip_controller_configure(&transport, &config, 42, NULL) == 1);
    assert(wr_eoip_controller_configure(NULL, &config, 42, &master) == 1);
    assert(master == 0);
    assert(wr_eoip_controller_remove(NULL, 0, 42) == 1);
    assert(wr_eoip_controller_create(NULL, &config) == 1);
    assert(wr_eoip_controller_query(NULL, 0, &observation) == 0);

    /* The real transport refuses nothing to send and an unknown interface. */
    assert(wr_eoip_socket_talk(NULL, NULL, 0, sequence) != 0);
    links[0].present = 0;
    assert(wr_eoip_build_owned_delete(request, sizeof(request), 2000000U, WR_EOIP_SEQUENCE_DELETE, &length));
    assert(wr_eoip_socket_talk(NULL, request, length, WR_EOIP_SEQUENCE_DELETE) != 0);

    snprintf(path, sizeof(path), "%s/lock", directory);
    unlink(path);
    assert(rmdir(directory) == 0);
    puts("PASS EoIP controller: slot mapping, owned create/delete requests, verified lifecycle and refusal paths");
    return 0;
}