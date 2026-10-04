#ifndef WR_BAND_CHILD_OWNER_H
#define WR_BAND_CHILD_OWNER_H
#include <sys/types.h>
/* Only a PID obtained when this caller spawned the actual steering daemon.
 * SIGCHLD is blocked only during bounded observation and its mask restored.
 * Caller must preserve status if the generic reaper runs before this call.
 * ECHILD/missing PID never proves radio OFF.
 * Zero means this specific child exited normally with daemon status 0:
 * both driver OFF acknowledgements. Never-enabled completion uses status 3.
 * Timeout keeps the PID for subsequent observation; no SIGKILL fallback. */
int wr_band_child_stop(pid_t *owned_pid, unsigned timeout_ms);
/* Register exactly one spawned daemon while SIGCHLD is blocked, before
 * restoring the pre-fork mask. The reaper records its waitpid status. */
int wr_band_child_track(pid_t pid);
void wr_band_child_reaped(pid_t pid, int status);
/* Fixed executable and argument list; success means spawned, not ready/active.
 * Caller must then await service/driver readiness and handle exec failure. */
int wr_band_child_spawn(pid_t *, const char *radio2g, const char *radio5g);
/* One bounded observation of our tracked live child and its authenticated
 * ACTIVE phase. Failure never discards ownership or proves driver OFF. */
int wr_band_child_ready(pid_t owned_pid);
/* Spawn and await ACTIVE from the tracked child. On failure preserve its PID
 * and exit record for verified stop/cleanup. Caller must not alter profiles
 * until cleanup confirms OFF. Maximum time is timeout_ms plus one 2s query. */
int wr_band_child_start_verified(pid_t *, const char *, const char *, unsigned timeout_ms);
#endif
