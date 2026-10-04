#define _POSIX_C_SOURCE 200809L
#include "child-owner.h"
#include "control-client.h"
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include <ctype.h>
#include <string.h>
#include <net/if.h>
#ifndef WR_BAND_DAEMON_PATH
#define WR_BAND_DAEMON_PATH "/usr/sbin/wr-band-steering"
#endif
static volatile sig_atomic_t tracked_pid, completed, exit_status;
static int interface_valid(const char *name)
{
    size_t i, n;
    if (!name) return 0;
    n=strnlen(name,IF_NAMESIZE);
    if (!n || n>=IF_NAMESIZE) return 0;
    for(i=0;i<n;++i) if (!isalnum((unsigned char)name[i]) && name[i]!='_' && name[i]!='-' && name[i]!='.') return 0;
    return 1;
}
int wr_band_child_spawn(pid_t *owned_pid, const char *radio2g, const char *radio5g)
{
    sigset_t blocked, previous, clean; pid_t pid; long maxfd, fd; int saved;
    if (!owned_pid || *owned_pid || tracked_pid || !interface_valid(radio2g) ||
        !interface_valid(radio5g) || !strcmp(radio2g,radio5g)) { errno=EINVAL; return -1; }
    maxfd=sysconf(_SC_OPEN_MAX); if(maxfd<0) return -1;
    sigemptyset(&blocked); sigaddset(&blocked,SIGCHLD);
    if(sigprocmask(SIG_BLOCK,&blocked,&previous)) return -1;
    pid=fork();
    if(pid==0) {
        sigemptyset(&clean);
        if(sigprocmask(SIG_SETMASK,&clean,0)) _exit(127);
        for(fd=3;fd<maxfd;++fd) close((int)fd);
        execl(WR_BAND_DAEMON_PATH,"wr-band-steering","--foreground",radio2g,radio5g,(char *)0);
        _exit(127);
    }
    saved=errno;
    if(pid>0) {
        /* Registration precedes unblocking, so even an immediate exec failure
         * cannot be consumed by the generic reaper before ownership exists. */
        completed=0; exit_status=0; tracked_pid=(sig_atomic_t)pid; *owned_pid=pid;
    }
    if(sigprocmask(SIG_SETMASK,&previous,0)) return -1;
    errno=saved; return pid<0 ? -1 : 0;
}
int wr_band_child_track(pid_t pid)
{
    sigset_t current;
    if (pid <= 1 || (pid_t)(sig_atomic_t)pid != pid || tracked_pid) { errno=EINVAL; return -1; }
    if (sigprocmask(SIG_SETMASK, 0, &current)) return -1;
    if (sigismember(&current, SIGCHLD) != 1) { errno=EPERM; return -1; }
    completed=0; exit_status=0; tracked_pid=(sig_atomic_t)pid; return 0;
}
void wr_band_child_reaped(pid_t pid, int status)
{
    if (tracked_pid && pid==(pid_t)tracked_pid) { exit_status=status; completed=1; }
}
static int owned_alive(pid_t pid)
{
    int status;
    pid_t found;
    if (pid <= 1 || pid != (pid_t)tracked_pid) { errno = EINVAL; return -1; }
    if (completed) { errno = ECHILD; return -1; }
    do { found = waitpid(pid, &status, WNOHANG); } while (found < 0 && errno == EINTR);
    if (found == pid) {
        wr_band_child_reaped(pid, status);
        errno = ECHILD; return -1;
    }
    return found < 0 ? -1 : 0;
}
int wr_band_child_ready(pid_t owned_pid)
{
    sigset_t blocked, previous;
    int result = -1, saved;
    sigemptyset(&blocked); sigaddset(&blocked, SIGCHLD);
    if (sigprocmask(SIG_BLOCK, &blocked, &previous)) return -1;
    if (!owned_alive(owned_pid) && !wr_band_control_active(owned_pid))
        result = owned_alive(owned_pid);
    saved = errno;
    if (sigprocmask(SIG_SETMASK, &previous, 0)) return -1;
    errno = saved; return result;
}
static int finish(pid_t *pid, int status)
{
    if (*pid==(pid_t)tracked_pid) { tracked_pid=0; completed=0; }
    *pid=0;
    if (WIFEXITED(status) && WEXITSTATUS(status)==0) return 0;
    errno=EIO; return -1;
}
static int milliseconds(uint64_t *out)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return -1;
    *out = (uint64_t)t.tv_sec * 1000 + (uint64_t)t.tv_nsec / 1000000;
    return 0;
}
static int wait_owned(pid_t *owned_pid, unsigned timeout_ms)
{
    uint64_t start, now; int status, signalled = 0; pid_t found;
    struct timespec delay = {0, 20000000};
    if (!owned_pid || *owned_pid <= 1 || !timeout_ms || timeout_ms > 60000) {
        errno = EINVAL; return -1;
    }
    if (milliseconds(&start)) return -1;
    for (;;) {
        if (completed && *owned_pid==(pid_t)tracked_pid) return finish(owned_pid,exit_status);
        found = waitpid(*owned_pid, &status, WNOHANG);
        if (found == *owned_pid) {
            return finish(owned_pid,status);
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
int wr_band_child_stop(pid_t *owned_pid, unsigned timeout_ms)
{
    sigset_t blocked, previous; int result, saved;
    sigemptyset(&blocked); sigaddset(&blocked, SIGCHLD);
    /* rc's generic reaper must not consume this child's status while waiting. */
    if (sigprocmask(SIG_BLOCK, &blocked, &previous)) return -1;
    result = wait_owned(owned_pid, timeout_ms); saved = errno;
    if (sigprocmask(SIG_SETMASK, &previous, 0)) return -1;
    errno = saved; return result;
}
