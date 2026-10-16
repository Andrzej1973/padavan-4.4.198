#ifndef WR_VPN_PROFILE_RESOURCES_H
#define WR_VPN_PROFILE_RESOURCES_H

#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Persistent ID space, not a claim about how many active tunnels RAM permits.
 * IDs are global across WG/AWG. Legacy wg0/wg1 and table 51 stay separate.
 * These names are candidates: inventory/ownership must be checked before use.
 */
#define WR_VPN_PROFILE_ID_MAX 999u
enum wr_vpn_protocol { WR_VPN_WIREGUARD = 1, WR_VPN_AMNEZIAWG = 2 };
struct wr_vpn_resources {
    unsigned int id;
    enum wr_vpn_protocol protocol;
    uint32_t table, mark, priority_main, priority_tunnel;
    char label[16], interface[16], chain[24], chain_remote[24], chain_mark[24];
    char clients[32], remote[32], exclude[32], dns[32];
    char storage[64], runtime[64], lock[64];
};

/* Only canonical decimal IDs are accepted in HTTP/CLI/storage references. */
static inline int wr_vpn_profile_id(const char *text, unsigned int *out)
{
    unsigned int value = 0;
    const unsigned char *p = (const unsigned char *)text;
    if (!p || !out || *p < '1' || *p > '9') return 0;
    for (; *p; ++p) {
        if (*p < '0' || *p > '9') return 0;
        value = value * 10u + (unsigned int)(*p - '0');
        if (value > WR_VPN_PROFILE_ID_MAX) return 0;
    }
    *out = value;
    return 1;
}

static inline int wr_vpn_resource_name(char *out, size_t size,
                                     const char *format, unsigned int id)
{
    int n = snprintf(out, size, format, id);
    return n >= 0 && (size_t)n < size;
}

static inline int wr_vpn_resources_make(struct wr_vpn_resources *out,
                                       unsigned int id,
                                       enum wr_vpn_protocol protocol)
{
    struct wr_vpn_resources r;
    if (!out || id == 0 || id > WR_VPN_PROFILE_ID_MAX ||
        (protocol != WR_VPN_WIREGUARD && protocol != WR_VPN_AMNEZIAWG)) return 0;
    memset(&r, 0, sizeof(r));
    r.id = id; r.protocol = protocol;
    r.table = 20000u + id;
    r.mark = UINT32_C(0x57560000) | id;
    r.priority_main = 20000u + 2u * (id - 1u);
    r.priority_tunnel = r.priority_main + 1u;
#define WR_VPN_NAME(field, format) \
    if (!wr_vpn_resource_name(r.field, sizeof(r.field), format, id)) return 0
    WR_VPN_NAME(label, protocol == WR_VPN_WIREGUARD ? "WG%u" : "AWG%u");
    WR_VPN_NAME(interface, "wrvpn%u");
    WR_VPN_NAME(chain, "WRV%u");
    WR_VPN_NAME(chain_remote, "WRV%u_R");
    WR_VPN_NAME(chain_mark, "WRV%u_M");
    WR_VPN_NAME(clients, "wrv%u.clients");
    WR_VPN_NAME(remote, "wrv%u.remote");
    WR_VPN_NAME(exclude, "wrv%u.exclude");
    WR_VPN_NAME(dns, "wrv%u.dns");
    WR_VPN_NAME(storage, "/etc/storage/wrvpn/%u");
    WR_VPN_NAME(runtime, "/var/run/wrvpn/%u");
    WR_VPN_NAME(lock, "/var/lock/wrvpn-%u.lock");
#undef WR_VPN_NAME
    *out = r;
    return 1;
}

/* Compare allocated profile bundles. Foreign/kernel inventory checks are a
 * separate mandatory activation preflight; this function does not reserve.
 */
static inline int wr_vpn_resources_conflict(const struct wr_vpn_resources *a,
                                           const struct wr_vpn_resources *b)
{
    const char *ac[3], *bc[3], *as[4], *bs[4];
    unsigned int i, j;
    if (!a || !b) return 1;
    if (a->id == b->id || a->table == b->table || a->mark == b->mark ||
        a->priority_main == b->priority_main || a->priority_main == b->priority_tunnel ||
        a->priority_tunnel == b->priority_main || a->priority_tunnel == b->priority_tunnel ||
        !strcmp(a->interface,b->interface) || !strcmp(a->storage,b->storage) ||
        !strcmp(a->runtime,b->runtime) || !strcmp(a->lock,b->lock)) return 1;
    ac[0]=a->chain; ac[1]=a->chain_remote; ac[2]=a->chain_mark;
    bc[0]=b->chain; bc[1]=b->chain_remote; bc[2]=b->chain_mark;
    as[0]=a->clients; as[1]=a->remote; as[2]=a->exclude; as[3]=a->dns;
    bs[0]=b->clients; bs[1]=b->remote; bs[2]=b->exclude; bs[3]=b->dns;
    for (i=0;i<3;i++) for (j=0;j<3;j++) if (!strcmp(ac[i],bc[j])) return 1;
    for (i=0;i<4;i++) for (j=0;j<4;j++) if (!strcmp(as[i],bs[j])) return 1;
    return 0;
}
#endif
