#define _GNU_SOURCE
#include "loop.h"
#include "listener.h"
#include "transport.h"
#include <errno.h>
#include <fcntl.h>
#include <net/if.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/file.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
static volatile sig_atomic_t stopping;
struct runtime {
    int command_fd, listener_fd;
    struct wr_band_route routes[2];
    uint8_t buffer[65536];
};
static void stop_signal(int signal_number) { (void)signal_number; stopping = 1; }
static int clock_ms(void *ctx, uint64_t *out)
{
    struct timespec t; (void)ctx;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return -1;
    if (t.tv_sec < 0 || (uint64_t)t.tv_sec > (UINT64_MAX - 1000) / 1000 ||
        t.tv_nsec < 0 || t.tv_nsec >= 1000000000) { errno = EOVERFLOW; return -1; }
    *out = (uint64_t)t.tv_sec * 1000 + (uint64_t)t.tv_nsec / 1000000; return 0;
}
static int send_command(size_t radio, enum wr_band_protocol protocol,
                         const struct wr_band_request *request, void *ctx)
{
    struct runtime *r = ctx;
    if (radio >= 2 || protocol != r->routes[radio].protocol) { errno = EINVAL; return -1; }
    return wr_band_send(r->command_fd, protocol, request);
}
static int receive_events(void *ctx, wr_band_event_callback callback, void *owner)
{
    struct runtime *r = ctx;
    return wr_band_receive(r->listener_fd, r->buffer, sizeof(r->buffer), r->routes, 2, callback, owner);
}
static int wait_events(void *ctx, int milliseconds)
{
    struct runtime *r = ctx; struct pollfd p;
    int result;
    memset(&p, 0, sizeof(p)); p.fd = r->listener_fd; p.events = POLLIN;
    result = poll(&p, 1, milliseconds);
    if (result < 0) return -1;
    if (p.revents & (POLLERR | POLLHUP | POLLNVAL)) { errno = EIO; return -1; }
    return result;
}
static int requested_stop(void *ctx) { (void)ctx; return stopping != 0; }
static int owner_lock(void)
{
    struct stat st; char pid[32]; int fd, length, saved;
    fd = open("/var/run/wr-band-steering.lock", O_RDWR | O_CREAT | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (fd < 0) return -1;
    if (fstat(fd, &st)) { saved = errno; close(fd); errno = saved; return -1; }
    if (!S_ISREG(st.st_mode) || st.st_uid != 0 || st.st_nlink != 1 || (st.st_mode & 077)) {
        close(fd); errno = EPERM; return -1;
    }
    if (flock(fd, LOCK_EX | LOCK_NB)) { saved = errno; close(fd); errno = saved; return -1; }
    length = snprintf(pid, sizeof(pid), "%ld\n", (long)getpid());
    if (ftruncate(fd, 0) || write(fd, pid, (size_t)length) != length) {
        saved = errno ? errno : EIO; close(fd); errno = saved; return -1;
    }
    /* Keep the inode: unlinking a lock can allow a second independent owner. */
    return fd;
}
int main(int argc, char **argv)
{
    static struct runtime runtime;
    static struct wr_band_coordinator coordinator;
    struct wr_band_radio_config radios[2] = {{WR_MT76X3, "", 2}, {WR_MT76X2, "", 1}};
    const struct wr_band_policy_config policy = {-70, 1500, 3000, 10000, 30000};
    const struct wr_band_loop_io io = {clock_ms, receive_events, wait_events, requested_stop};
    struct sigaction action; struct wr_band_request check = {0};
    uint8_t bytes[80]; uint64_t now; size_t i;
    int lock_fd = -1, result = 1;
    runtime.command_fd = runtime.listener_fd = -1;
    if (argc == 2 && !strcmp(argv[1], "--help")) {
        puts("Usage: wr-band-steering --foreground <mt76x3-2g-interface> <mt76x2-5g-interface>\n"
             "Candidate: requires prepared drivers and exclusive initialized profiles; no profile setup is performed.");
        return 0;
    }
    if (argc != 4 || strcmp(argv[1], "--foreground")) { fprintf(stderr, "Use --help for usage.\n"); return 2; }
    if (geteuid() != 0) { fprintf(stderr, "Root is required.\n"); return 2; }
    for (i = 0; i < 2; ++i) {
        check.command = WR_QUERY; check.interface_name = argv[2 + i];
        if (wr_band_encode(radios[i].protocol, &check, bytes, sizeof(bytes)) < 0) return 2;
        memcpy(radios[i].name, argv[2 + i], strlen(argv[2 + i]) + 1);
        runtime.routes[i].protocol = radios[i].protocol;
        runtime.routes[i].ifindex = if_nametoindex(radios[i].name);
        if (!runtime.routes[i].ifindex) { perror("interface"); return 2; }
    }
    if (runtime.routes[0].ifindex == runtime.routes[1].ifindex) return 2;
    lock_fd = owner_lock(); if (lock_fd < 0) { perror("owner lock"); goto done; }
    memset(&action, 0, sizeof(action)); action.sa_handler = stop_signal; sigemptyset(&action.sa_mask);
    if (sigaction(SIGTERM, &action, NULL) || sigaction(SIGINT, &action, NULL)) { perror("signal setup"); goto done; }
    runtime.listener_fd = wr_band_listener_open();
    if (runtime.listener_fd < 0) { perror("event listener"); goto done; }
    runtime.command_fd = socket(AF_INET, SOCK_DGRAM | SOCK_CLOEXEC, 0);
    if (runtime.command_fd < 0 || clock_ms(NULL, &now)) { perror("command/clock setup"); goto done; }
    if (wr_band_coordinator_init(&coordinator, radios, &policy, now, send_command, &runtime)) goto done;
    result = wr_band_loop_run(&coordinator, &io, &runtime) ? 1 : 0;
    if (result) fprintf(stderr, "Steering failed; disable was best effort and radio OFF is unverified.\n");
done:
    if (runtime.command_fd >= 0) close(runtime.command_fd);
    if (runtime.listener_fd >= 0) close(runtime.listener_fd);
    if (lock_fd >= 0) close(lock_fd);
    return result;
}
