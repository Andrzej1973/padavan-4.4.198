#ifndef WR_IOT_PRECREATED_DOWN_RECOVERY_H
#define WR_IOT_PRECREATED_DOWN_RECOVERY_H
#include "precreated-down-wire.h"
/* Process context only. Caller owns cold admission/fence/profile and has
 * proved Main UP was never attempted. Allows a pending normal shutdown;
 * never clears that signal or grants generation/open permission. */
int wr_iot_initial_down_recovery_current(const unsigned char *,const struct wr_iot_down_result *);
#endif
