#ifndef WR_EOIP_STATUS_RUNTIME_H
#define WR_EOIP_STATUS_RUNTIME_H
/* Read-only child queries: the HTTP event loop only reads a nonblocking pipe
 * and reaps its own PID. No commands, NVRAM, interfaces or files are changed. */
#include "netlink-query.h"
#include <dirent.h>
#include <limits.h>
#include <signal.h>
#include <sys/wait.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

struct wr_eoip_status_packet {
    int present[8];
    struct wr_eoip_observation slots[8];
};
struct wr_eoip_status_runtime {
    pid_t pid;
    int fd, failed, valid;
    size_t received;
    uint64_t started, sampled;
    unsigned char bytes[sizeof(struct wr_eoip_status_packet) + 1];
    struct wr_eoip_status_packet cached;
};
static void wr_eoip_status_init(struct wr_eoip_status_runtime *r)
{ memset(r, 0, sizeof(*r)); r->fd = -1; }

static int wr_eoip_status_child_fds(int keep)
{
    DIR *dir = opendir("/proc/self/fd");
    struct dirent *entry;
    unsigned count = 0;
    int ok = 1;
    if (!dir) return 0;
    for (;;) {
        char *end;
        long fd;
        errno = 0; entry = readdir(dir);
        if (!entry) { if (errno) ok = 0; break; }
        if (++count > 1024) { ok = 0; break; }
        errno = 0; fd = strtol(entry->d_name, &end, 10);
        if (!errno && !*end && fd > 2 && fd <= INT_MAX && fd != keep && fd != dirfd(dir))
            close((int)fd);
    }
    closedir(dir);
    return ok;
}
static void wr_eoip_status_cancel(struct wr_eoip_status_runtime *r)
{
    if (r->pid > 0) { kill(r->pid, SIGKILL); r->failed = 1; }
    if (r->fd >= 0) { close(r->fd); r->fd = -1; }
}
static int wr_eoip_status_start(struct wr_eoip_status_runtime *r, uint64_t now)
{
    int p[2], flags;
    pid_t pid;
    if (r->pid > 0 || pipe(p)) return 0;
    flags = fcntl(p[0], F_GETFL);
    if (flags < 0 || fcntl(p[0], F_SETFL, flags | O_NONBLOCK) < 0) {
        close(p[0]); close(p[1]); return 0;
    }
    pid = fork();
    if (pid < 0) { close(p[0]); close(p[1]); return 0; }
    if (!pid) {
        struct wr_eoip_status_packet packet;
        unsigned slot;
        size_t offset = 0;
        int nullfd;
        close(p[0]);
        signal(SIGTERM, SIG_DFL); signal(SIGPIPE, SIG_DFL); signal(SIGCHLD, SIG_DFL);
        nullfd = open("/dev/null", O_RDWR);
        if (nullfd < 0 || dup2(nullfd, 0) < 0 || dup2(nullfd, 1) < 0 || dup2(nullfd, 2) < 0 ||
            !wr_eoip_status_child_fds(p[1])) _exit(126);
        memset(&packet, 0, sizeof(packet));
        for (slot = 0; slot < 8; slot++) {
            char name[16], owner[32];
            snprintf(name, sizeof(name), "wr-eoip%u", slot);
            snprintf(owner, sizeof(owner), "wr-eoip:%u:v1", slot);
            packet.present[slot] = wr_eoip_query_link(name, owner, &packet.slots[slot]);
        }
        while (offset < sizeof(packet)) {
            ssize_t n = write(p[1], ((char *)&packet) + offset, sizeof(packet) - offset);
            if (n < 0 && errno == EINTR) continue;
            if (n <= 0) _exit(126);
            offset += (size_t)n;
        }
        close(p[1]); _exit(0);
    }
    close(p[1]);
    r->pid = pid; r->fd = p[0]; r->started = now; r->received = 0; r->failed = 0;
    return 1;
}
static void wr_eoip_status_tick(struct wr_eoip_status_runtime *r, uint64_t now)
{
    int status;
    pid_t reaped;
    if (r->pid <= 0) return;
    if (r->fd >= 0 && r->received < sizeof(r->bytes)) {
        ssize_t n = read(r->fd, r->bytes + r->received, sizeof(r->bytes) - r->received);
        if (n > 0) r->received += (size_t)n;
        else if (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
            wr_eoip_status_cancel(r);
        if (r->received > sizeof(r->cached)) wr_eoip_status_cancel(r);
    }
    reaped = waitpid(r->pid, &status, WNOHANG);
    if (!reaped) {
        if (!r->failed && (now < r->started || now - r->started >= 20)) wr_eoip_status_cancel(r);
        return;
    }
    if (reaped < 0 && errno == EINTR) return;
    if (reaped == r->pid && r->fd >= 0 && r->received < sizeof(r->bytes)) {
        ssize_t n = read(r->fd, r->bytes + r->received, sizeof(r->bytes) - r->received);
        if (n > 0) r->received += (size_t)n;
        else if (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK) r->failed = 1;
    }
    r->valid = reaped == r->pid && WIFEXITED(status) && !WEXITSTATUS(status) &&
        !r->failed && now >= r->started && r->received == sizeof(r->cached);
    if (r->valid) { memcpy(&r->cached, r->bytes, sizeof(r->cached)); r->sampled = r->started; }
    if (r->fd >= 0) close(r->fd);
    r->fd = -1; r->pid = 0;
}
#endif
