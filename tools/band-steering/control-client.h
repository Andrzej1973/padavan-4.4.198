#ifndef WR_BAND_CONTROL_CLIENT_H
#define WR_BAND_CONTROL_CLIENT_H
#include <sys/types.h>
/* Fixed local endpoint, root credentials and optional expected daemon PID.
 * Zero means a validated reply, not ACTIVE or confirmed OFF. Caller must
 * compare the returned phase. Maximum observation is two seconds.
 * STOP acknowledges a request only. No shell, spawn or driver commands. */
int wr_band_control_request(pid_t expected_pid, int stop, char output[64]);
#endif
