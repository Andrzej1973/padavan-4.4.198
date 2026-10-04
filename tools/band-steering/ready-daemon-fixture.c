#define _POSIX_C_SOURCE 200809L
#include "control.h"
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <string.h>
#ifndef WR_READY_ENDPOINT
#error Fixture endpoint required
#endif
static volatile sig_atomic_t stopping;
static void stop_signal(int signal) { (void)signal; stopping = 1; }
/* Host-only stand-in: real foreground argv/IPC, never driver access. */
int main(int argc, char **argv)
{
    struct wr_band_control c;
    struct pollfd p;
    struct sigaction action = {0};
    enum wr_band_phase phase;
    int requested = 0;
    if (argc != 4 || strcmp(argv[3], "rai0")) return 5;
    if (!strcmp(argv[1], "--quiesce")) {
        /* Stand-in exit contract only; actual driver ACKs are session-tested. */
        if (!strcmp(argv[2], "ra0")) return 0;
        if (!strcmp(argv[2], "ra1")) return 3;
        return 5;
    }
    if (strcmp(argv[1], "--foreground")) return 5;
    if (!strcmp(argv[2], "ra0")) phase = WR_ACTIVE;
    else if (!strcmp(argv[2], "ra1")) phase = WR_QUERYING;
    else return 5;
    action.sa_handler = stop_signal; sigemptyset(&action.sa_mask);
    if (sigaction(SIGTERM, &action, 0) || wr_band_control_open(&c, WR_READY_ENDPOINT)) return 6;
    p.fd = c.fd; p.events = POLLIN;
    while (!stopping && !requested) {
        int result;
        p.revents = 0;
        result = poll(&p, 1, 1000);
        if (result < 0 && errno == EINTR) continue;
        if (result < 0) return 7;
        if (result && wr_band_control_receive(&c, phase, &requested) < 0) return 8;
    }
    wr_band_control_close(&c);
    return 0;
}
