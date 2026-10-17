#ifndef WR_VPN_RUNTIME_STATE_H
#define WR_VPN_RUNTIME_STATE_H
#include "resources.h"
#include "store.h"
/* Volatile session identity. This API never creates/deletes network objects.
 * Hold one global operation lock across inventory, kernel actions and records.
 * Persistent profile locks are acquired after this lock, never in reverse.
 */
struct wr_vpn_runtime { int root, lock; };
struct wr_vpn_session {
    unsigned int id;
    enum wr_vpn_protocol protocol;
    uint64_t revision;
    uint32_t index; /* zero = intent recorded before exclusive link creation */
    unsigned char nonce[16];
};
enum wr_vpn_runtime_result {
    WR_VPN_RUNTIME_OK, WR_VPN_RUNTIME_ABSENT, WR_VPN_RUNTIME_BUSY,
    WR_VPN_RUNTIME_INVALID, WR_VPN_RUNTIME_STALE, WR_VPN_RUNTIME_IO
};
enum wr_vpn_runtime_result wr_vpn_runtime_lock(const char *,struct wr_vpn_runtime *);
void wr_vpn_runtime_unlock(struct wr_vpn_runtime *);
enum wr_vpn_runtime_result wr_vpn_runtime_read(struct wr_vpn_runtime *,unsigned int,struct wr_vpn_session *);
/* expected NULL means create only. Replacement requires exact old identity. */
enum wr_vpn_runtime_result wr_vpn_runtime_put(struct wr_vpn_runtime *,const struct wr_vpn_session *,const struct wr_vpn_session *expected);
enum wr_vpn_runtime_result wr_vpn_runtime_clear(struct wr_vpn_runtime *,const struct wr_vpn_session *expected);
int wr_vpn_session_new(struct wr_vpn_session *,unsigned int,enum wr_vpn_protocol,uint64_t);
int wr_vpn_session_owner(const struct wr_vpn_session *,char *,size_t);

/* Last successfully applied configuration, kept as the rollback source for the
 * next apply. Same privacy rules as the session file: private directory, 0600,
 * single link, atomic rename and symlink refusal. It carries private keys, so
 * it is never logged or served.
 */
enum wr_vpn_runtime_result wr_vpn_runtime_snapshot_put(struct wr_vpn_runtime *,
    const struct wr_vpn_record *);
enum wr_vpn_runtime_result wr_vpn_runtime_snapshot_get(struct wr_vpn_runtime *,
    unsigned int, struct wr_vpn_record *);
#endif
