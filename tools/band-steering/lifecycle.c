#include "lifecycle.h"
int wr_band_lifecycle_apply(const struct wr_band_lifecycle_ops *ops, void *context,
                            int enabled, struct wr_band_apply_result *result)
{
    if (!result) return -1;
    result->state = WR_APPLY_REJECTED; result->off_confirmed = 0;
    if (!ops || !ops->quiesce_verified || !ops->write_both_profiles ||
        !ops->initialize_both_radios || (enabled != 0 && enabled != 1) ||
        (enabled && (!ops->validate_snapshot || !ops->start_verified))) return -1;
    if (enabled && ops->validate_snapshot(context)) return -1;
    result->state = WR_APPLY_OFF_UNVERIFIED;
    if (ops->quiesce_verified(context)) return -1;
    result->off_confirmed = 1; result->state = WR_APPLY_OFF_CONFIRMED;
    if (ops->write_both_profiles(context, enabled)) {
        result->state = WR_APPLY_PROFILE_ERROR; return -1;
    }
    /* Initializing enabled profiles can change driver state even on failure. */
    result->off_confirmed = !enabled;
    if (ops->initialize_both_radios(context) || (enabled && ops->start_verified(context))) {
        result->state = WR_APPLY_START_ERROR;
        result->off_confirmed = !ops->quiesce_verified(context);
        return -1;
    }
    result->state = enabled ? WR_APPLY_RUNNING : WR_APPLY_OFF_CONFIRMED;
    return 0;
}
