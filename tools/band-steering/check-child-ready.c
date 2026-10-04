#define _POSIX_C_SOURCE 200809L
#include "child-owner.h"
#include "control-client.h"
#include "control.h"
#include <assert.h>
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>
static void check(const char *path, enum wr_band_phase phase)
{
    int pipes[2], stop = 0, status;
    pid_t pid;
    sigset_t blocked, previous, after;
    char ready, reply[64];
    assert(!pipe(pipes));
    sigemptyset(&blocked); sigaddset(&blocked, SIGCHLD);
    assert(!sigprocmask(SIG_BLOCK, &blocked, &previous));
    pid = fork(); assert(pid >= 0);
    if (!pid) {
        struct wr_band_control c;
        struct pollfd p;
        close(pipes[0]);
        assert(!sigprocmask(SIG_SETMASK, &previous, 0));
        assert(!wr_band_control_open(&c, path));
        assert(write(pipes[1], "R", 1) == 1); close(pipes[1]);
        p.fd = c.fd; p.events = POLLIN;
        while (!stop) {
            p.revents = 0;
            assert(poll(&p, 1, 4000) == 1 && (p.revents & POLLIN));
            assert(wr_band_control_receive(&c, phase, &stop) >= 0);
        }
        wr_band_control_close(&c); _exit(0);
    }
    assert(!wr_band_child_track(pid));
    assert(!sigprocmask(SIG_SETMASK, &previous, 0));
    close(pipes[1]); assert(read(pipes[0], &ready, 1) == 1); close(pipes[0]);
    assert(wr_band_child_ready(pid + 1) == -1 && errno == EINVAL);
    if (phase == WR_ACTIVE) assert(!wr_band_child_ready(pid));
    else assert(wr_band_child_ready(pid) == -1 && errno == EAGAIN);
    assert(!sigprocmask(SIG_SETMASK, 0, &after));
    assert(sigismember(&after, SIGCHLD) == sigismember(&previous, SIGCHLD));
    assert(!wr_band_control_request(pid, 1, reply));
    assert(waitpid(pid, &status, 0) == pid);
    wr_band_child_reaped(pid, status);
    assert(wr_band_child_ready(pid) == -1 && errno == ECHILD);
    assert(!wr_band_child_stop(&pid, 1000) && !pid);
}
int main(int argc, char **argv)
{
    assert(argc == 2 && geteuid() == 0);
    check(argv[1], WR_ACTIVE);
    check(argv[1], WR_QUERYING);
    puts("PASS owned child ACTIVE readiness, intermediate phase rejection, exit rejection and mask restoration; no driver access");
    return 0;
}
