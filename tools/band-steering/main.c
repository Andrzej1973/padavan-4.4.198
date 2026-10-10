#define _GNU_SOURCE
#include "loop.h"
#include "listener.h"
#include "transport.h"
#include "control.h"
#include "action-observer.h"
#include "grant-evidence.h"
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
    struct wr_band_action_observer observations;
    struct wr_band_control control;
    struct wr_band_coordinator *coordinator;
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
static int actual_command(enum wr_band_protocol protocol,const struct wr_band_request *request,void *context)
{
    struct runtime *r=context;return wr_band_send(r->command_fd,protocol,request);
}
static int send_command(size_t radio, enum wr_band_protocol protocol,
                         const struct wr_band_request *request, void *ctx)
{
    struct runtime *r = ctx;
    if (radio >= 2 || protocol != r->routes[radio].protocol) { errno = EINVAL; return -1; }
    uint64_t now;
    if(clock_ms(NULL,&now))return wr_band_send(r->command_fd,protocol,request);
    return wr_action_steering_command(&r->observations.reporter,(unsigned int)radio,now,
                                    protocol,request,actual_command,r);
}
struct observed_dispatch {struct runtime *runtime;wr_band_event_callback callback;void *owner;};
static void observed_event(size_t radio,const struct wr_band_event *event,void *context)
{
    struct observed_dispatch *d=context;struct wr_band_coordinator *c=d->runtime->coordinator;
    int pending=0,saved;struct wr_action_event evidence;
    if(c&&c->session.phase==WR_ACTIVE&&radio<2&&event->type==WR_EVENT_GRANT&&event->table_index<WR_BAND_CLIENT_LIMIT){
        pending=wr_band_grant_evidence(&c->grants,radio,event,0);
    }
    d->callback(radio,event,d->owner);saved=errno;
    if(pending&&c->session.phase==WR_ACTIVE){
        const struct wr_grant_radio *g=&c->grants.slots[event->table_index].radio[radio];
        if(wr_band_grant_evidence(&c->grants,radio,event,1)){
            memset(&evidence,0,sizeof(evidence));evidence.source=WR_ACTION_STEERING;
            evidence.operation=WR_ACTION_ALLOW;evidence.stage=WR_ACTION_DRIVER_ACK;
            evidence.radio=(unsigned char)radio;evidence.cookie=event->cookie;
            evidence.uptime_ms=g->verified_at;memcpy(evidence.mac,event->mac,6);
            /* This proves candidate-table state only, never association/roam. */
            wr_action_report(&d->runtime->observations.reporter,&evidence);
        }
    }
    errno=saved;
}
static int receive_events(void *ctx, wr_band_event_callback callback, void *owner)
{
    struct runtime *r = ctx;
    struct observed_dispatch dispatch={r,callback,owner};
    return wr_band_receive(r->listener_fd, r->buffer, sizeof(r->buffer), r->routes, 2, observed_event, &dispatch);
}
static int wait_events(void *ctx, int milliseconds)
{
    struct runtime *r = ctx; struct pollfd p[2];
    int result, stop = 0; unsigned count;
    memset(p, 0, sizeof(p)); p[0].fd = r->listener_fd; p[0].events = POLLIN;
    p[1].fd = r->control.fd; p[1].events = POLLIN;
    result = poll(p, 2, milliseconds);
    if (result < 0) return -1;
    if ((p[0].revents | p[1].revents) & (POLLERR | POLLHUP | POLLNVAL)) { errno = EIO; return -1; }
    if (p[1].revents & POLLIN) {
        for (count = 0; count < 4; ++count) {
            int received = wr_band_control_receive(&r->control, r->coordinator->session.phase, &stop);
            if (received < 0) return -1;
            if (!received) break;
        }
        if (stop) stopping = 1;
    }
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
    int lock_fd = -1, result = 1, quiesce = 0;
    runtime.command_fd = runtime.listener_fd = -1;
    wr_band_action_init(&runtime.observations);
    runtime.control.fd = -1; runtime.coordinator = &coordinator;
    if (argc == 2 && !strcmp(argv[1], "--help")) {
        puts("Usage: wr-band-steering --foreground|--quiesce <mt76x3-2g-interface> <mt76x2-5g-interface>\n"
             "Candidate: requires prepared drivers and exclusive initialized profiles; no profile setup is performed.");
        return 0;
    }
    if (argc != 4 || (strcmp(argv[1], "--foreground") && strcmp(argv[1], "--quiesce"))) {
        fprintf(stderr, "Use --help for usage.\n"); return 2;
    }
    quiesce = !strcmp(argv[1], "--quiesce");
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
    if (wr_band_control_open(&runtime.control, "/var/run/wr-band-steering/control")) {
        perror("control endpoint"); goto done;
    }
    if (wr_band_coordinator_init(&coordinator, radios, &policy, now, send_command, &runtime)) goto done;
    if (quiesce && wr_band_session_quiesce(&coordinator.session, now)) goto done;
    result = wr_band_loop_run(&coordinator, &io, &runtime) ? 1 : 0;
    if (!result && !wr_band_session_off_confirmed(&coordinator.session)) {
        result = 3;
        fprintf(stderr, "Session completed without both OFF acknowledgements; radio OFF is unverified.\n");
    } else if (result) fprintf(stderr, "Steering failed; disable was best effort and radio OFF is unverified.\n");
done:
    wr_action_channel_close(&runtime.observations.channel);
    wr_band_control_close(&runtime.control);
    if (runtime.command_fd >= 0) close(runtime.command_fd);
    if (runtime.listener_fd >= 0) close(runtime.listener_fd);
    if (lock_fd >= 0) close(lock_fd);
    return result;
}

