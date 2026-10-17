#ifndef WR_VPN_CONFIG_TRANSACTION_H
#define WR_VPN_CONFIG_TRANSACTION_H
#include "config-apply.h"
#include "runtime-state.h"

/* One protocol-config transaction: take the operation lock, verify the session
 * identity (id, protocol, revision, index, nonce) against the caller's copy,
 * apply, read the kernel back, and confirm the session is still ours.
 *
 * The caller's session copy is a compare-and-swap expectation: a session that
 * changed in between makes the transaction stale instead of overwriting
 * somebody else's work. A record whose readback differs is replaced by the
 * optional previous record, and the rollback itself must read back.
 *
 * This covers the native protocol configuration only. Link creation, addresses,
 * routes, DNS, rollback policy and connectivity acceptance belong to the
 * controller; this function never creates or deletes an interface.
 */
enum wr_vpn_transaction_result {
    WR_VPN_TRANSACTION_DONE,             /* applied, readback matched, session ours */
    WR_VPN_TRANSACTION_ABSENT,           /* no runtime session for the profile */
    WR_VPN_TRANSACTION_BUSY,             /* operation lock held elsewhere */
    WR_VPN_TRANSACTION_STALE,            /* session or record identity moved on */
    WR_VPN_TRANSACTION_REFUSED,          /* validation or plan refused; untouched */
    WR_VPN_TRANSACTION_UNKNOWN,          /* transport or ownership unconfirmed */
    WR_VPN_TRANSACTION_MISMATCH,         /* not applied; previous record verified */
    WR_VPN_TRANSACTION_ROLLBACK_FAILED,  /* not applied; previous record unverified */
    WR_VPN_TRANSACTION_IO,               /* runtime bookkeeping failed */
    WR_VPN_TRANSACTION_UNSAVED           /* applied and verified, rollback source stale */
};

enum wr_vpn_transaction_result wr_vpn_config_transaction(
    const char *runtime_root, const struct wr_vpn_record *record,
    const struct wr_vpn_session *expected, const struct wr_vpn_record *rollback);

#endif
