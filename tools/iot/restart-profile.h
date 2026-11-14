/* Read-only fixed-path cold profile check under the retained service guard.
 * Caller serializes and retains the immutable desired request.
 * Checks saved/requested credentials and generated third-BSS content. Never
 * generates/writes a profile, changes NVRAM, opens a BSS or proves loaded keys. */
#ifndef WR_IOT_RESTART_PROFILE_H
#define WR_IOT_RESTART_PROFILE_H
#include "request.h"
int wr_iot_restart_profile_current(const struct wr_iot_request *);
#endif
