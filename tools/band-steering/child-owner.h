#ifndef WR_BAND_CHILD_OWNER_H
#define WR_BAND_CHILD_OWNER_H
#include <sys/types.h>
/* Only a PID obtained when this caller spawned the actual steering daemon.
 * SIGCHLD is blocked only during bounded observation and its mask restored.
 * Caller must preserve status if the generic reaper runs before this call.
 * ECHILD/missing PID never proves radio OFF.
 * Zero means this specific child exited normally with daemon success status.
 * Timeout keeps the PID for subsequent observation; no SIGKILL fallback. */
int wr_band_child_stop(pid_t *owned_pid, unsigned timeout_ms);
#endif
