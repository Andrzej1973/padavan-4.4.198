/* Read-only profile rows for the VPN page. Mutating actions are separate.
 * The fixed manager binary is executed without a shell, with a bounded
 * timeout, a bounded output buffer and no inherited descriptors. */
#include <dirent.h>
#include <errno.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#ifndef WR_VPN_PROFILE_BIN
#define WR_VPN_PROFILE_BIN "/usr/sbin/wr-vpn-profile"
#endif
#ifndef WR_VPN_LIST_TIMEOUT_MS
#define WR_VPN_LIST_TIMEOUT_MS 3000
#endif
#include "vpn-profiles-render.h"

static long long wr_vpn_web_ms(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC,&now)) return -1;
    return (long long)now.tv_sec*1000+now.tv_nsec/1000000;
}

static void wr_vpn_web_closefds(void)
{
    DIR *dir;struct dirent *entry;int scan;long fd;char *end;
    dir=opendir("/proc/self/fd");
    if (!dir) return;
    scan=dirfd(dir);
    for (;;) {
        errno=0;entry=readdir(dir);
        if (!entry) break;
        errno=0;fd=strtol(entry->d_name,&end,10);
        if (!errno && !*end && fd>2 && fd!=scan && fd<=INT_MAX) close((int)fd);
    }
    closedir(dir);
}

/* Runs the fixed manager and captures bounded stdout. Returns non-zero only
 * for an exit status of zero with a complete (not truncated) capture. */
static int wr_vpn_web_run(const char *const argv[],char *out,size_t capacity)
{
    int pipefd[2],status;pid_t child;size_t used=0;long long began;int ok=0;
    if (!argv || !out || capacity<2) return 0;
    if (pipe(pipefd)) return 0;
    child=fork();
    if (child<0) { close(pipefd[0]);close(pipefd[1]);return 0; }
    if (!child) {
        if (dup2(pipefd[1],1)<0 || dup2(pipefd[1],2)<0) _exit(127);
        wr_vpn_web_closefds();
        execv(argv[0],(char *const *)argv);
        _exit(127);
    }
    close(pipefd[1]);
    began=wr_vpn_web_ms();
    if (began<0) goto failed;
    for (;;) {
        struct pollfd pfd;int ready;ssize_t got;
        long long now=wr_vpn_web_ms();
        if (now<began || now-began>=WR_VPN_LIST_TIMEOUT_MS) break;
        pfd.fd=pipefd[0];pfd.events=POLLIN;pfd.revents=0;
        ready=poll(&pfd,1,50);
        if (ready<0) { if (errno==EINTR) continue;break; }
        if (ready>0 && (pfd.revents&POLLIN)) {
            if (used+1>=capacity) break; /* truncated: refuse the result */
            got=read(pipefd[0],out+used,capacity-1-used);
            if (got>0) { used+=(size_t)got;continue; }
            if (got==0) { ok=1;break; }
            if (errno==EINTR) continue;
            break;
        }
        if (ready>0 && (pfd.revents&(POLLHUP|POLLERR))) { ok=1;break; }
    }
    if (!ok) goto failed;
    for (;;) {
        pid_t waited=waitpid(child,&status,WNOHANG);
        struct timespec delay={0,20000000};
        long long now;
        if (waited==child) break;
        if (waited<0 && errno!=EINTR) { close(pipefd[0]);return 0; }
        now=wr_vpn_web_ms();
        if (now<began || now-began>=WR_VPN_LIST_TIMEOUT_MS) goto failed;
        nanosleep(&delay,NULL);
    }
    close(pipefd[0]);
    out[used]=0;
    return WIFEXITED(status) && WEXITSTATUS(status)==0;
failed:
    kill(child,SIGKILL);
    while (waitpid(child,&status,0)<0 && errno==EINTR) {}
    close(pipefd[0]);
    return 0;
}

/* Renders one table row per stored profile: id, label, revision. */
static int ej_wr_vpn_profile_rows(int eid,webs_t wp,int argc,char **argv)
{
    const char *args[]={WR_VPN_PROFILE_BIN,"list",NULL};
    char output[2048],rows[2048];int rendered;
    (void)eid;(void)argc;(void)argv;
    if (!get_login_safe()) return websWrite(wp,"<tr><td colspan=\"3\">unavailable</td></tr>");
    if (!wr_vpn_web_run(args,output,sizeof(output)))
        return websWrite(wp,"<tr><td colspan=\"3\">unavailable</td></tr>");
    rendered=wr_vpn_web_render(output,rows,sizeof(rows));
    if (rendered<0) return websWrite(wp,"<tr><td colspan=\"3\">unavailable</td></tr>");
    if (!rendered) return websWrite(wp,"<tr><td colspan=\"3\">none</td></tr>");
    websWrite(wp,"%s",rows);
    return 0;
}
