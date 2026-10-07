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

struct apply_context {
    struct wr_band_service_owner *owner;
    const char *radio2g, *radio5g;
    const struct wr_band_lifecycle_ops *radio_ops;
    void *radio_context;
};
static int validate(void *p)
{
    struct apply_context *c = p;
    return c->radio_ops->validate_snapshot(c->radio_context);
}
static int quiesce(void *p)
{
    struct apply_context *c = p;
    return wr_band_service_quiesce(c->owner, c->radio2g, c->radio5g);
}
static int profiles(void *p, int enabled)
{
    struct apply_context *c = p;
    return c->radio_ops->write_both_profiles(c->radio_context, enabled);
}
static int radios(void *p)
{
    struct apply_context *c = p;
    return c->radio_ops->initialize_both_radios(c->radio_context);
}
static int start(void *p)
{
    struct apply_context *c = p;
    return wr_band_service_start(c->owner, c->radio2g, c->radio5g);
}
int wr_band_service_apply(struct wr_band_service_owner *owner,
    const char *radio2g, const char *radio5g,
    const struct wr_band_lifecycle_ops *radio_ops, void *radio_context,
    int enabled, struct wr_band_apply_result *result)
{
    struct apply_context context = {owner, radio2g, radio5g, radio_ops, radio_context};
    struct wr_band_lifecycle_ops ops = {validate, quiesce, profiles, radios, start};
    if (!owner || !radio2g || !radio5g || !radio_ops ||
        !radio_ops->write_both_profiles || !radio_ops->initialize_both_radios ||
        (enabled && !radio_ops->validate_snapshot)) {
        if (result) { result->state = WR_APPLY_REJECTED; result->off_confirmed = 0; }
        errno = EINVAL; return -1;
    }
    return wr_band_lifecycle_apply(&ops, &context, enabled, result);
}
