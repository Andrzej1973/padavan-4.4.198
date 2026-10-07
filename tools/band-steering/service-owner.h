#ifndef WR_BAND_SERVICE_OWNER_H
#define WR_BAND_SERVICE_OWNER_H
#include <sys/types.h>
#include "lifecycle.h"
/* rc owns one instance and serializes all lifecycle calls. Preserve this
 * instance, including a failed child's PID, until verified observation. */
struct wr_band_service_owner { pid_t pid; };
int wr_band_service_quiesce(struct wr_band_service_owner *, const char *, const char *);
int wr_band_service_start(struct wr_band_service_owner *, const char *, const char *);
/* Caller serializes settings and provides paired profile/radio callbacks.
 * Process ownership, OFF proof and ACTIVE proof use the actual child helpers. */
int wr_band_service_apply(struct wr_band_service_owner *, const char *, const char *,
    const struct wr_band_lifecycle_ops *, void *, int, struct wr_band_apply_result *);
#endif
