#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "config-apply.h"
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#ifndef WR_VPN_CONTROL_WG
#define WR_VPN_CONTROL_WG "/usr/libexec/wrvpn/wg"
#endif
#ifndef WR_VPN_CONTROL_AWG
#define WR_VPN_CONTROL_AWG "/usr/libexec/wrvpn/awg"
#endif
#ifndef WR_VPN_READBACK_WG
#define WR_VPN_READBACK_WG "/usr/libexec/wrvpn/readback-wg"
#endif
#ifndef WR_VPN_READBACK_AWG
#define WR_VPN_READBACK_AWG "/usr/libexec/wrvpn/readback-awg"
#endif
#ifndef WR_VPN_APPLY_TIMEOUT_MS
#define WR_VPN_APPLY_TIMEOUT_MS 5000
#endif
static void erase(void *data,size_t size)
{ volatile unsigned char *p=data;while (size--) *p++=0; }
static long long milliseconds(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC,&now)) return -1;
    return (long long)now.tv_sec*1000+now.tv_nsec/1000000;
}
static void execute(int input,const char *path,const char *interface,int verify,uint32_t index)
{
    DIR *dir;struct dirent *entry;struct rlimit core={0,0};
    int nullfd,scan;long fd;char *end;
    char index_text[16];char *argv[5];
    char *const env[]={"LC_ALL=C",NULL};
    snprintf(index_text,sizeof(index_text),"%u",index);
    argv[0]=(char *)path;
    if (verify) { argv[1]=(char *)interface;argv[2]=index_text;argv[3]=NULL; }
    else { argv[1]="setconf";argv[2]=(char *)interface;argv[3]="/proc/self/fd/0"; }
    argv[4]=NULL;
    if (dup2(input,0)<0) _exit(127);
    nullfd=open("/dev/null",O_RDWR|O_CLOEXEC);
    if (nullfd<0 || dup2(nullfd,1)<0 || dup2(nullfd,2)<0 ||
        fcntl(0,F_SETFD,0) || fcntl(1,F_SETFD,0) || fcntl(2,F_SETFD,0) ||
        setrlimit(RLIMIT_CORE,&core)) _exit(127);
    dir=opendir("/proc/self/fd");if (!dir) _exit(127);scan=dirfd(dir);
    for (;;) {
        errno=0;entry=readdir(dir);
        if (!entry) { if (errno) _exit(127);break; }
        errno=0;fd=strtol(entry->d_name,&end,10);
        if (!errno && !*end && fd>2 && fd<=INT_MAX && fd!=scan)
            if (close((int)fd) && errno!=EBADF) _exit(127);
    }
    if (closedir(dir)) _exit(127);
    execve(path,argv,env);_exit(127);
}
static enum wr_vpn_apply_result run(const struct wr_vpn_record *record,int verify,uint32_t index,int *mismatch)
{
    struct wr_vpn_config_plan *plan=calloc(1,sizeof(*plan));
    enum wr_vpn_validation validation;enum wr_vpn_apply_result result=WR_VPN_APPLY_NOT_STARTED;
    char temporary[]="/tmp/wrvpn-config-XXXXXX";
    const char *path;int fd=-1,status;pid_t child,done;
    long long began,now;size_t size,sent=0;
    if (!plan) return result;
    validation=wr_vpn_prepare_config(record,plan);
    if (validation!=WR_VPN_VALID) {
        if (validation==WR_VPN_REJECTED) result=WR_VPN_APPLY_REFUSED;
        goto finish;
    }
    /* Native tools must never resolve a name during this mutation. */
    if (plan->hostname_endpoints) { result=WR_VPN_APPLY_REFUSED;goto finish; }
    path=record->protocol==WR_VPN_WIREGUARD?WR_VPN_CONTROL_WG:WR_VPN_CONTROL_AWG;
    if (verify) path=record->protocol==WR_VPN_WIREGUARD?WR_VPN_READBACK_WG:WR_VPN_READBACK_AWG;
    began=milliseconds();if (began<0) goto finish;
    fd=mkstemp(temporary);if (fd<0) goto finish;
    /* Unlink before any secret is written. The child reopens its inherited
     * regular file via procfs; no secret path is left for crash cleanup. */
    if (unlink(temporary)) goto finish;
    if (fcntl(fd,F_SETFD,FD_CLOEXEC)) goto finish;
    size=strlen(plan->native);
    while (sent<size) {
        ssize_t n=write(fd,plan->native+sent,size-sent);
        if (n<0 && errno==EINTR) continue;
        if (n<=0) goto finish;
        sent+=(size_t)n;
    }
    if (lseek(fd,0,SEEK_SET)<0) goto finish;
    child=fork();if (child<0) goto finish;
    if (!child) execute(fd,path,plan->resources.interface,verify,index);
    result=WR_VPN_APPLY_UNKNOWN;
    for (;;) {
        done=waitpid(child,&status,WNOHANG);
        if (done==child) {
            if (WIFEXITED(status) && WEXITSTATUS(status)==0) result=WR_VPN_APPLY_ACKNOWLEDGED;
            if (verify && WIFEXITED(status) && WEXITSTATUS(status)==2) *mismatch=1;
            break;
        }
        /* An external reaper may have released this PID. Never signal it. */
        if (done<0 && errno!=EINTR) break;
        now=milliseconds();
        if (now<0 || now-began>=WR_VPN_APPLY_TIMEOUT_MS) {
            kill(child,SIGKILL);
            while (waitpid(child,&status,0)<0 && errno==EINTR) {}
            break;
        }
        (void)poll(NULL,0,20);
    }
finish:
    if (fd>=0) close(fd);
    erase(plan,sizeof(*plan));free(plan);return result;
}
enum wr_vpn_apply_result wr_vpn_config_apply(const struct wr_vpn_record *record)
{ return run(record,0,0,NULL); }
enum wr_vpn_readback_result wr_vpn_config_readback(const struct wr_vpn_record *record,uint32_t index)
{
    int mismatch=0;enum wr_vpn_apply_result result;
    if (!index) return WR_VPN_READBACK_UNKNOWN;
    result=run(record,1,index,&mismatch);
    if (result==WR_VPN_APPLY_ACKNOWLEDGED) return WR_VPN_READBACK_MATCH;
    return mismatch?WR_VPN_READBACK_MISMATCH:WR_VPN_READBACK_UNKNOWN;
}
