#include "service-owner.h"
#include "child-owner.h"
#include <errno.h>

int wr_band_service_quiesce(struct wr_band_service_owner *owner,
                            const char *radio2g, const char *radio5g)
{
    int stopped;
    if (!owner) { errno = EINVAL; return -1; }
    if (owner->pid) {
        stopped = wr_band_child_stop(&owner->pid, 5000);
        /* An unverified exit may clear a reaped PID. A fresh OFF-only daemon
         * can still establish the actual current driver state. A surviving
         * child must retain ownership and prevents another spawn. */
        if (owner->pid) return -1;
        if (!stopped) return 0;
    }
    return wr_band_child_quiesce(&owner->pid, radio2g, radio5g);
}

int wr_band_service_start(struct wr_band_service_owner *owner,
                          const char *radio2g, const char *radio5g)
{
    if (!owner || owner->pid) { errno = EINVAL; return -1; }
    return wr_band_child_start_verified(&owner->pid, radio2g, radio5g, 5000);
}
