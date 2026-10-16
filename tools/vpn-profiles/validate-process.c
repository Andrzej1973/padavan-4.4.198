#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "validate-process.h"
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifndef WR_VPN_VALIDATE_WG
#define WR_VPN_VALIDATE_WG "/usr/libexec/wrvpn/validate-wg"
#endif
#ifndef WR_VPN_VALIDATE_AWG
#define WR_VPN_VALIDATE_AWG "/usr/libexec/wrvpn/validate-awg"
#endif
#ifndef WR_VPN_VALIDATE_TIMEOUT_MS
#define WR_VPN_VALIDATE_TIMEOUT_MS 5000
#endif

static long long wr_milliseconds(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC,&now)) return -1;
    return (long long)now.tv_sec*1000+now.tv_nsec/1000000;
}
static void wr_validator_exec(int input,const char *path)
{
    DIR *dir; struct dirent *entry;
    struct rlimit core={0,0};
    int nullfd,scan; long value; char *end;
    char *const argv[]={(char *)path,NULL};
    char *const env[]={"LC_ALL=C","ASAN_OPTIONS=detect_leaks=1:exitcode=98",
        "UBSAN_OPTIONS=halt_on_error=1:exitcode=97",NULL};
    if (dup2(input,STDIN_FILENO)<0) _exit(127);
    nullfd=open("/dev/null",O_RDWR|O_CLOEXEC);
    if (nullfd<0 || dup2(nullfd,STDOUT_FILENO)<0 || dup2(nullfd,STDERR_FILENO)<0) _exit(127);
    if (fcntl(0,F_SETFD,0) || fcntl(1,F_SETFD,0) || fcntl(2,F_SETFD,0) || setrlimit(RLIMIT_CORE,&core)) _exit(127);
    /* Do not pass management sockets, store handles or locks to the parser. */
    dir=opendir("/proc/self/fd"); if (!dir) _exit(127); scan=dirfd(dir);
    for (;;) {
        errno=0; entry=readdir(dir);
        if (!entry) { if (errno) _exit(127); break; }
        errno=0; value=strtol(entry->d_name,&end,10);
        if (!errno && !*end && value>2 && value<=INT_MAX && value!=scan)
            if (close((int)value) && errno!=EBADF) _exit(127);
    }
    if (closedir(dir)) _exit(127);
    execve(path,argv,env); _exit(127);
}
enum wr_vpn_validation wr_vpn_validate(enum wr_vpn_protocol protocol,
                                     const void *data,size_t size)
{
    const char *path;
    const unsigned char *bytes=data;
    size_t sent=0; int pair[2],flags,status=0,write_open=1,transport_ok=1;
    pid_t child,done; long long began,now;
    if (!data || !size || size>WR_VPN_CONFIG_MAX || memchr(data,0,size)) return WR_VPN_REJECTED;
    if (protocol==WR_VPN_WIREGUARD) path=WR_VPN_VALIDATE_WG;
    else if (protocol==WR_VPN_AMNEZIAWG) path=WR_VPN_VALIDATE_AWG;
    else return WR_VPN_REJECTED;
    began=wr_milliseconds(); if (began<0) return WR_VPN_VALIDATOR_FAILED;
    if (socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,pair)) return WR_VPN_VALIDATOR_FAILED;
    child=fork();
    if (child<0) { close(pair[0]); close(pair[1]); return WR_VPN_VALIDATOR_FAILED; }
    if (!child) wr_validator_exec(pair[0],path);
    close(pair[0]);
    flags=fcntl(pair[1],F_GETFL);
    if (flags<0 || fcntl(pair[1],F_SETFL,flags|O_NONBLOCK)) goto failed;
    for (;;) {
        struct pollfd descriptor={pair[1],POLLOUT,0};
        now=wr_milliseconds(); if (now<0 || now-began>=WR_VPN_VALIDATE_TIMEOUT_MS) goto failed;
        done=waitpid(child,&status,WNOHANG);
        if (done==child) break;
        /* ECHILD means ownership was lost (e.g. an external reaper). Never
         * signal that PID after it could have been recycled. */
        if (done<0 && errno!=EINTR) { close(pair[1]); return WR_VPN_VALIDATOR_FAILED; }
        if (write_open && sent<size) {
            ssize_t n=send(pair[1],bytes+sent,size-sent,MSG_NOSIGNAL);
            if (n>0) sent+=(size_t)n;
            else if (n<0 && errno!=EAGAIN && errno!=EWOULDBLOCK && errno!=EINTR) {
                transport_ok=0; shutdown(pair[1],SHUT_WR); write_open=0;
            }
        }
        if (write_open && sent==size) { shutdown(pair[1],SHUT_WR); write_open=0; }
        if (!write_open) descriptor.fd=-1;
        if (poll(&descriptor,1,20)<0 && errno!=EINTR) goto failed;
    }
    close(pair[1]);
    if (!WIFEXITED(status)) return WR_VPN_VALIDATOR_FAILED;
    if (WEXITSTATUS(status)==2) return WR_VPN_REJECTED;
    if (WEXITSTATUS(status)==0 && transport_ok && sent==size) return WR_VPN_VALID;
    return WR_VPN_VALIDATOR_FAILED;
failed:
    close(pair[1]); kill(child,SIGKILL);
    while (waitpid(child,&status,0)<0 && errno==EINTR) {}
    return WR_VPN_VALIDATOR_FAILED;
}
