#define _GNU_SOURCE
#include "control.h"
#include <errno.h>
#include <stddef.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>
const char *wr_band_control_status(enum wr_band_phase phase)
{
    switch (phase) {
    case WR_QUERYING: return "querying\n";
    case WR_ENABLING: return "enabling\n";
    case WR_ACTIVE: return "active\n";
    case WR_STOPPING: return "stopping\n";
    case WR_STOPPED: return "stopped_session_complete\n";
    case WR_FAILED: return "failed_off_unverified\n";
    default: return "unknown_off_unverified\n";
    }
}
void wr_band_control_close(struct wr_band_control *c)
{
    struct stat st;
    if (!c) return;
    if (c->fd >= 0) close(c->fd);
    if (c->inode && !lstat(c->path, &st) && S_ISSOCK(st.st_mode) &&
        st.st_dev == c->device && st.st_ino == c->inode && st.st_uid == geteuid()) unlink(c->path);
    c->fd = -1; c->inode = 0;
}
int wr_band_control_open(struct wr_band_control *c, const char *path)
{
    struct sockaddr_un address; struct stat st; char parent[108], *slash;
    size_t length; int one = 1, saved;
    if (!c || !path) { errno = EINVAL; return -1; }
    memset(c, 0, sizeof(*c)); c->fd = -1;
    length = strnlen(path, sizeof(c->path));
    if (!length || length >= sizeof(c->path) || path[0] != '/') { errno = EINVAL; return -1; }
    memcpy(parent, path, length + 1); slash = strrchr(parent, '/');
    if (!slash || slash == parent || !slash[1]) { errno = EINVAL; return -1; }
    *slash = 0;
    if (mkdir(parent, 0700) && errno != EEXIST) return -1;
    if (lstat(parent, &st)) return -1;
    if (!S_ISDIR(st.st_mode) || st.st_uid != geteuid() || (st.st_mode & 0777) != 0700) { errno = EPERM; return -1; }
    if (!lstat(path, &st)) {
        if (!S_ISSOCK(st.st_mode) || st.st_uid != geteuid() || (st.st_mode & 0777) != 0600 || st.st_nlink != 1) {
            errno = EPERM; return -1;
        }
        if (unlink(path)) return -1;
    } else if (errno != ENOENT) return -1;
    c->fd = socket(AF_UNIX, SOCK_DGRAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (c->fd < 0) return -1;
    memset(&address, 0, sizeof(address)); address.sun_family = AF_UNIX;
    memcpy(address.sun_path, path, length + 1); memcpy(c->path, path, length + 1);
    if (setsockopt(c->fd, SOL_SOCKET, SO_PASSCRED, &one, sizeof(one)) ||
        bind(c->fd, (struct sockaddr *)&address, (socklen_t)(offsetof(struct sockaddr_un, sun_path) + length + 1))) goto fail;
    if (lstat(path, &st)) goto fail;
    c->device = st.st_dev; c->inode = st.st_ino;
    if (chmod(path, 0600)) goto fail;
    return 0;
fail:
    saved = errno; wr_band_control_close(c); errno = saved; return -1;
}
int wr_band_control_receive(struct wr_band_control *c, enum wr_band_phase phase, int *stop_requested)
{
    struct sockaddr_un peer; struct msghdr message; struct iovec io;
    union { struct cmsghdr alignment; char bytes[CMSG_SPACE(sizeof(struct ucred))]; } ancillary;
    struct cmsghdr *header; struct ucred credentials; char request[16];
    const char *reply; ssize_t n; int authenticated = 0;
    if (!c || c->fd < 0 || !stop_requested) { errno = EINVAL; return -1; }
    memset(&message, 0, sizeof(message)); memset(&peer, 0, sizeof(peer));
    io.iov_base = request; io.iov_len = sizeof(request);
    message.msg_name = &peer; message.msg_namelen = sizeof(peer);
    message.msg_iov = &io; message.msg_iovlen = 1;
    message.msg_control = ancillary.bytes; message.msg_controllen = sizeof(ancillary.bytes);
    n = recvmsg(c->fd, &message, MSG_DONTWAIT);
    if (n < 0) return errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR ? 0 : -1;
    if (message.msg_flags & (MSG_TRUNC | MSG_CTRUNC)) return 1;
    if (message.msg_namelen <= offsetof(struct sockaddr_un, sun_path) ||
        message.msg_namelen > sizeof(peer) || peer.sun_family != AF_UNIX) return 1;
    for (header = CMSG_FIRSTHDR(&message); header; header = CMSG_NXTHDR(&message, header)) {
        if (header->cmsg_level == SOL_SOCKET && header->cmsg_type == SCM_CREDENTIALS &&
            header->cmsg_len == CMSG_LEN(sizeof(credentials))) {
            memcpy(&credentials, CMSG_DATA(header), sizeof(credentials));
            authenticated = credentials.uid == geteuid() && credentials.pid > 0;
        }
    }
    if (!authenticated) return 1;
    if (n == 7 && !memcmp(request, "STATUS\n", 7)) reply = wr_band_control_status(phase);
    else if (n == 5 && !memcmp(request, "STOP\n", 5)) {
        *stop_requested = 1; reply = "stop_requested_off_unverified\n";
    } else reply = "invalid_request\n";
    /* A vanished/slow control client must not interrupt driver heartbeat ticks. */
    (void)sendto(c->fd, reply, strlen(reply), MSG_DONTWAIT | MSG_NOSIGNAL,
                 (struct sockaddr *)&peer, message.msg_namelen);
    return 1;
}

