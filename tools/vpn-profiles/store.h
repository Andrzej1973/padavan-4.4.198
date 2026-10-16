#ifndef WR_VPN_PROFILE_STORE_H
#define WR_VPN_PROFILE_STORE_H
#include <stddef.h>
#include <stdint.h>
#include "resources.h"

#define WR_VPN_CONFIG_MAX 16384u
enum wr_vpn_store_result {
    WR_VPN_STORE_OK, WR_VPN_STORE_BUSY, WR_VPN_STORE_NOT_FOUND,
    WR_VPN_STORE_EXISTS, WR_VPN_STORE_STALE, WR_VPN_STORE_INVALID,
    WR_VPN_STORE_IO, WR_VPN_STORE_COMMITTED_UNSYNCED
};
struct wr_vpn_record {
    unsigned int id;
    enum wr_vpn_protocol protocol;
    uint64_t revision;
    size_t size;
    unsigned char config[WR_VPN_CONFIG_MAX];
};

/* root must already be a private directory owned by the effective UID.
 * Each operation opens its own nonblocking lock description. Never unlink it.
 * Payload is data, never shell code; semantic WG/AWG validation is separate.
 * This does not start/stop tunnels or commit RAM storage to router flash.
 */
int wr_vpn_store_open(const char *root);
enum wr_vpn_store_result wr_vpn_store_get(int root, unsigned int id,
                                        struct wr_vpn_record *out);
/* expected=0 creates a never-used ID; otherwise compare-and-replace.
 * Deleted IDs remain tombstones: old requests cannot target a new profile.
 */
enum wr_vpn_store_result wr_vpn_store_put(int root, unsigned int id,
    enum wr_vpn_protocol protocol, const void *config, size_t size,
    uint64_t expected, uint64_t *revision);
enum wr_vpn_store_result wr_vpn_store_delete(int root, unsigned int id,
    uint64_t expected, uint64_t *revision);
#endif
