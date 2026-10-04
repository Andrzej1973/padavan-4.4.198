#define _POSIX_C_SOURCE 200809L
#include "child-owner.h"
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <sys/wait.h>
#include <time.h>
static int milliseconds(uint64_t *out)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return -1;
    *out = (uint64_t)t.tv_sec * 1000 + (uint64_t)t.tv_nsec / 1000000;
    return 0;
}
int wr_band_child_stop(pid_t *owned_pid, unsigned timeout_ms)
{
    uint64_t start, now; int status, signalled = 0; pid_t found;
    struct timespec delay = {0, 20000000};
    if (!owned_pid || *owned_pid <= 1 || !timeout_ms || timeout_ms > 60000) {
        errno = EINVAL; return -1;
    }
    if (milliseconds(&start)) return -1;
    for (;;) {
        found = waitpid(*owned_pid, &status, WNOHANG);
        if (found == *owned_pid) {
            *owned_pid = 0;
            if (WIFEXITED(status) && WEXITSTATUS(status) == 0) return 0;
            errno = EIO; return -1;
        }
        if (found < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        /* The unreaped child cannot have its PID reused between wait/kill. */
        if (!signalled) {
            if (kill(*owned_pid, SIGTERM) && errno != ESRCH) return -1;
            signalled = 1;
        }
        if (milliseconds(&now)) return -1;
        if (now < start || now - start >= timeout_ms) { errno = ETIMEDOUT; return -1; }
        (void)nanosleep(&delay, 0);
    }
}
