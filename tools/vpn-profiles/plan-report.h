#ifndef WR_VPN_PLAN_REPORT_H
#define WR_VPN_PLAN_REPORT_H
#include "config-plan.h"
#include "runtime-state.h"

/* Writes a reviewable, secret-free summary of what an apply would involve:
 * the requested configuration fields, the observed session and rollback
 * snapshot, and whether apply is currently possible.
 *
 * The native configuration, and therefore the private key, is never copied
 * into the output. This function performs no network or state changes beyond
 * running the pinned validator that the plan already uses.
 *
 * Returns non-zero on success; the output is truncated to capacity otherwise.
 */
int wr_vpn_plan_report(const struct wr_vpn_record *record,
    const struct wr_vpn_session *session, const struct wr_vpn_record *snapshot,
    char *out, size_t capacity);

#endif
