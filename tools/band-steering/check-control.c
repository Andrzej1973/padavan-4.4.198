#define _GNU_SOURCE
#include "control.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>
static void exchange(int fd, struct wr_band_control *c, const char *request,
                     enum wr_band_phase phase, const char *expected, int *stop)
{
    struct pollfd p = {fd, POLLIN, 0}; char reply[80]; ssize_t n;
    assert(send(fd, request, strlen(request), 0) == (ssize_t)strlen(request));
    assert(wr_band_control_receive(c, phase, stop) == 1);
    assert(poll(&p, 1, 100) == 1);
    n = recv(fd, reply, sizeof(reply) - 1, 0); assert(n > 0); reply[n] = 0;
    assert(!strcmp(reply, expected));
}
int main(void)
{
    char directory[] = "/tmp/wr-control-XXXXXX", path[108];
    struct wr_band_control c = {-1, "", 0, 0}; struct sockaddr_un peer, server;
    struct stat st; int fd, stop = 0; size_t size;
    assert(mkdtemp(directory)); assert(snprintf(path, sizeof(path), "%s/control", directory) > 0);
    assert(!wr_band_control_open(&c, path));
    assert(!lstat(path, &st) && S_ISSOCK(st.st_mode) && (st.st_mode & 0777) == 0600);
    assert(fcntl(c.fd, F_GETFL) & O_NONBLOCK); assert(fcntl(c.fd, F_GETFD) & FD_CLOEXEC);
    assert(wr_band_control_receive(&c, WR_ACTIVE, &stop) == 0 && !stop);
    fd = socket(AF_UNIX, SOCK_DGRAM | SOCK_CLOEXEC, 0); assert(fd >= 0);
    memset(&peer, 0, sizeof(peer)); peer.sun_family = AF_UNIX;
    assert(snprintf(peer.sun_path + 1, sizeof(peer.sun_path) - 1, "wr-check-control-%ld", (long)getpid()) > 0);
    size = offsetof(struct sockaddr_un, sun_path) + 1 + strlen(peer.sun_path + 1);
    assert(!bind(fd, (struct sockaddr *)&peer, (socklen_t)size));
    memset(&server, 0, sizeof(server)); server.sun_family = AF_UNIX; strcpy(server.sun_path, path);
    size = offsetof(struct sockaddr_un, sun_path) + strlen(path) + 1;
    assert(!connect(fd, (struct sockaddr *)&server, (socklen_t)size));
    exchange(fd, &c, "STATUS\n", WR_ACTIVE, "active\n", &stop); assert(!stop);
    exchange(fd, &c, "STATUS\n", WR_FAILED, "failed_off_unverified\n", &stop); assert(!stop);
    exchange(fd, &c, "STOP junk\n", WR_ACTIVE, "invalid_request\n", &stop); assert(!stop);
    assert(send(fd, "STOP\n01234567890123456789", 25, 0) == 25);
    assert(wr_band_control_receive(&c, WR_ACTIVE, &stop) == 1 && !stop);
    exchange(fd, &c, "STOP\n", WR_ACTIVE, "stop_requested_off_unverified\n", &stop); assert(stop);
    exchange(fd, &c, "STATUS\n", WR_STOPPED, "stopped_session_complete\n", &stop);
    close(fd); wr_band_control_close(&c); assert(lstat(path, &st) && errno == ENOENT);
    fd = open(path, O_CREAT | O_EXCL | O_WRONLY, 0600); assert(fd >= 0); close(fd);
    assert(wr_band_control_open(&c, path) == -1 && errno == EPERM);
    assert(!lstat(path, &st) && S_ISREG(st.st_mode)); wr_band_control_close(&c);
    assert(!unlink(path)); assert(!chmod(directory, 0755));
    assert(wr_band_control_open(&c, path) == -1 && errno == EPERM);
    assert(!rmdir(directory));
    puts("PASS real Unix control socket: credentials, bounded commands, status, stop request and private path");
    return 0;
}

