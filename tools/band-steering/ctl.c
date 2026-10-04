#define _GNU_SOURCE
#include <errno.h>
#include <poll.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>
#ifndef WR_CONTROL_DIRECTORY
#define WR_CONTROL_DIRECTORY "/var/run/wr-band-steering"
#endif
#define WR_CONTROL_ENDPOINT WR_CONTROL_DIRECTORY "/control"

/* Candidate local administration client. No driver IOCTLs or profile changes. */
int main(int argc, char **argv)
{
    const char *request, *endpoint = WR_CONTROL_ENDPOINT;
    struct sockaddr_un local, server;
    struct stat st;
    struct pollfd ready;
    struct msghdr message;
    struct iovec io;
    union { struct cmsghdr align; char bytes[CMSG_SPACE(sizeof(struct ucred))]; } ancillary;
    struct cmsghdr *header;
    struct ucred credentials;
    char reply[64];
    ssize_t n;
    int fd, one = 1, result = 1, authenticated = 0;
    if (argc == 2 && !strcmp(argv[1], "--help")) {
        puts("Usage: wr-band-steering-ctl status|stop\n"
             "STOP acknowledges a request, not proof that radios stopped steering.");
        return 0;
    }
    if (argc != 2 || (strcmp(argv[1], "status") && strcmp(argv[1], "stop"))) {
        fprintf(stderr, "Use --help for usage.\n"); return 2;
    }
    if (geteuid() != 0) { fprintf(stderr, "Root is required.\n"); return 2; }
    request = !strcmp(argv[1], "status") ? "STATUS\n" : "STOP\n";
    if (lstat(WR_CONTROL_DIRECTORY, &st) || !S_ISDIR(st.st_mode) ||
        st.st_uid != 0 || (st.st_mode & 0777) != 0700) {
        fprintf(stderr, "Control directory unavailable or invalid; radio state unverified.\n"); return 1;
    }
    if (lstat(endpoint, &st) || !S_ISSOCK(st.st_mode) || st.st_uid != 0 ||
        (st.st_mode & 0777) != 0600 || st.st_nlink != 1) {
        fprintf(stderr, "Control endpoint unavailable or invalid; radio state unverified.\n"); return 1;
    }
    fd = socket(AF_UNIX, SOCK_DGRAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
    if (fd < 0) { perror("control socket"); return 1; }
    memset(&local, 0, sizeof(local)); local.sun_family = AF_UNIX;
    /* Linux abstract address: kernel removes it on close; bind detects collisions. */
    n = snprintf(local.sun_path + 1, sizeof(local.sun_path) - 1,
                 "wr-band-steering-ctl-%ld", (long)getpid());
    if (n <= 0 || (size_t)n >= sizeof(local.sun_path) - 1) goto done;
    if (setsockopt(fd, SOL_SOCKET, SO_PASSCRED, &one, sizeof(one)) ||
        bind(fd, (struct sockaddr *)&local,
             (socklen_t)(offsetof(struct sockaddr_un, sun_path) + 1 + n))) goto error;
    memset(&server, 0, sizeof(server)); server.sun_family = AF_UNIX;
    memcpy(server.sun_path, endpoint, strlen(endpoint) + 1);
    if (connect(fd, (struct sockaddr *)&server,
                (socklen_t)(offsetof(struct sockaddr_un, sun_path) + strlen(endpoint) + 1))) goto error;
    if (send(fd, request, strlen(request), MSG_NOSIGNAL) != (ssize_t)strlen(request)) goto error;
    ready.fd = fd; ready.events = POLLIN; ready.revents = 0;
    /* A signal or timeout is an observation failure; do not resend STOP. */
    if (poll(&ready, 1, 2000) != 1 || !(ready.revents & POLLIN) ||
        (ready.revents & (POLLERR | POLLHUP | POLLNVAL))) {
        fprintf(stderr, "No valid control response; radio state unverified.\n"); goto done;
    }
    memset(&message, 0, sizeof(message));
    io.iov_base = reply; io.iov_len = sizeof(reply) - 1;
    message.msg_iov = &io; message.msg_iovlen = 1;
    message.msg_control = ancillary.bytes; message.msg_controllen = sizeof(ancillary.bytes);
    n = recvmsg(fd, &message, MSG_DONTWAIT);
    if (n <= 0 || message.msg_flags & (MSG_TRUNC | MSG_CTRUNC)) goto invalid;
    for (header = CMSG_FIRSTHDR(&message); header; header = CMSG_NXTHDR(&message, header)) {
        if (header->cmsg_level == SOL_SOCKET && header->cmsg_type == SCM_CREDENTIALS &&
            header->cmsg_len == CMSG_LEN(sizeof(credentials))) {
            memcpy(&credentials, CMSG_DATA(header), sizeof(credentials));
            authenticated = credentials.uid == 0 && credentials.pid > 0;
        }
    }
    if (!authenticated) goto invalid;
    reply[n] = 0;
    if (strlen(reply) != (size_t)n) goto invalid;
    if (!strcmp(argv[1], "stop")) {
        if (strcmp(reply, "stop_requested_off_unverified\n")) goto invalid;
    } else if (strcmp(reply, "querying\n") && strcmp(reply, "enabling\n") &&
               strcmp(reply, "active\n") && strcmp(reply, "stopping\n") &&
               strcmp(reply, "stopped_session_complete\n") &&
               strcmp(reply, "failed_off_unverified\n") &&
               strcmp(reply, "unknown_off_unverified\n")) goto invalid;
    if (fputs(reply, stdout) == EOF) goto error;
    result = 0; goto done;
invalid:
    fprintf(stderr, "Invalid control response; radio state unverified.\n"); goto done;
error:
    perror("control request");
done:
    close(fd); return result;
}
