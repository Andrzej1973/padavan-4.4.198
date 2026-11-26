/* Detached runner for one WebUI profile action. The HTTP process only starts
 * this worker, so a slow up/down never blocks the web server. */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifndef WR_VPN_MANAGER
#define WR_VPN_MANAGER "/usr/sbin/wr-vpn-profile"
#endif
#ifndef WR_VPN_SERVICE
#define WR_VPN_SERVICE "/usr/sbin/wr-vpn-profiles-service"
#endif
#ifndef WR_VPN_ACTION_ROOT
#define WR_VPN_ACTION_ROOT "/var/run/wrvpn/actions"
#endif
#ifndef WR_VPN_ACTION_TIMEOUT_MS
#define WR_VPN_ACTION_TIMEOUT_MS 30000
#endif
#ifndef WR_VPN_DNS_SYNC_TIMEOUT_MS
#define WR_VPN_DNS_SYNC_TIMEOUT_MS 5000
#endif

static long long now_ms(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC,&now)) return -1;
    return (long long)now.tv_sec*1000+now.tv_nsec/1000000;
}

static int run_dns_sync_once(void)
{
    char *const argv[]={(char *)WR_VPN_SERVICE,"dns-sync",NULL};
    char *const env[]={"LC_ALL=C",NULL};
    pid_t child,done;int status,nullfd;long long began;
    child=fork();
    if (child<0) return 1;
    if (!child) {
        nullfd=open("/dev/null",O_RDWR|O_CLOEXEC);
        if (nullfd<0 || dup2(nullfd,STDOUT_FILENO)<0 || dup2(nullfd,STDERR_FILENO)<0) _exit(127);
        execve(WR_VPN_SERVICE,argv,env);
        _exit(127);
    }
    began=now_ms();
    for (;;) {
        done=waitpid(child,&status,WNOHANG);
        if (done==child) return WIFEXITED(status) && WEXITSTATUS(status)==0?0:1;
        if (done<0 && errno!=EINTR) return 1;
        if (began<0 || now_ms()-began>=WR_VPN_DNS_SYNC_TIMEOUT_MS) {
            kill(child,SIGKILL);
            while (waitpid(child,&status,0)<0 && errno==EINTR) {}
            return 1;
        }
        (void)poll(NULL,0,20);
    }
}

static int run_dns_sync(void)
{
    int attempt;
    for (attempt=0;attempt<3;attempt++) {
        if (!run_dns_sync_once()) return 0;
        if (attempt<2) (void)poll(NULL,0,100);
    }
    return 1;
}

static void append_dns_sync_failure(char *output,size_t capacity,size_t *used)
{
    static const char message[]=" dnsmasq DNS sync failed";
    size_t length=sizeof(message)-1;
    if (*used+length>=capacity) return;
    memcpy(output+*used,message,length);*used+=length;output[*used]=0;
}

static int valid_id(const char *text,unsigned int *out)
{
    unsigned int value=0;const unsigned char *p=(const unsigned char *)text;
    if (!p || !out || *p<'1' || *p>'9') return 0;
    for (;*p;p++) {
        if (*p<'0' || *p>'9') return 0;
        value=value*10u+(unsigned int)(*p-'0');
        if (value>999u) return 0;
    }
    *out=value;return 1;
}

static int valid_protect(const char *text)
{
    size_t i,length;
    if (!text) return 1;
    length=strlen(text);
    if (length>200) return 0;
    for (i=0;i<length;i++) {
        char c=text[i];
        if (!((c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F')||
              c==':'||c=='.'||c=='/'||c==',')) return 0;
    }
    return 1;
}

static void write_state(const char *rootdir,unsigned int id,const char *state,
                        int code,const char *output)
{
    char temp[96],target[64];int fd;size_t used=0;char text[2200];
    snprintf(temp,sizeof(temp),".state-%u-%ld",id,(long)getpid());
    snprintf(target,sizeof(target),"%u",id);
    fd=openat(AT_FDCWD,rootdir,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if (fd<0) return;
    {
        int file=openat(fd,temp,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
        if (file<0) { close(fd);return; }
        used=(size_t)snprintf(text,sizeof(text),"state=%s\ncode=%d\noutput=",state,code);
        if (output && *output) {
            size_t i;
            for (i=0;output[i] && used+1<sizeof(text);i++)
                text[used++]=(output[i]=='\n'||output[i]=='\r')?' ':output[i];
        }
        text[used++]='\n';
        if (write(file,text,used)!=(ssize_t)used) { close(file);unlinkat(fd,temp,0);close(fd);return; }
        if (close(file)) { unlinkat(fd,temp,0);close(fd);return; }
        if (renameat(fd,temp,fd,target)) unlinkat(fd,temp,0);
    }
    close(fd);
}

int main(int argc,char **argv)
{
    unsigned int id;const char *action;const char *protect=NULL;
    const char *args[5];char *const env[]={"LC_ALL=C",NULL};
    char output[2048];size_t used=0;int pipefd[2],status,code=-1,timeout=0,overflow=0;
    pid_t child;long long began;
    if (argc<3 || argc>4) return 2;
    if (!valid_id(argv[1],&id)) return 2;
    action=argv[2];
    if (strcmp(action,"up") && strcmp(action,"down") && strcmp(action,"delete")) return 2;
    if (argc==4) { if (!valid_protect(argv[3])) return 2; protect=argv[3]; }
    if (mkdir(WR_VPN_ACTION_ROOT,0700) && errno!=EEXIST) return 3;
    {
        int dir=open(WR_VPN_ACTION_ROOT,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
        struct stat st;
        if (dir<0) return 3;
        if (fstat(dir,&st) || st.st_uid!=geteuid() || (st.st_mode&0777)!=0700) { close(dir);return 3; }
        close(dir);
    }
    write_state(WR_VPN_ACTION_ROOT,id,"running",-1,"");
    if (pipe(pipefd)) return 3;
    args[0]=WR_VPN_MANAGER;args[1]=action;args[2]=argv[1];
    args[3]=(!strcmp(action,"up")&&protect)?protect:NULL;
    args[4]=NULL;
    child=fork();
    if (child<0) { close(pipefd[0]);close(pipefd[1]);write_state(WR_VPN_ACTION_ROOT,id,"failed",-1,"");return 3; }
    if (!child) {
        int fd;
        if (dup2(pipefd[1],1)<0 || dup2(pipefd[1],2)<0) _exit(127);
        close(pipefd[0]);
        for (fd=3;fd<256;fd++) close(fd);
        execve(args[0],(char *const *)args,env);
        _exit(127);
    }
    close(pipefd[1]);
    began=now_ms();
    for (;;) {
        struct pollfd pfd;int ready;ssize_t got;
        pfd.fd=pipefd[0];pfd.events=POLLIN;pfd.revents=0;
        ready=poll(&pfd,1,50);
        if (ready<0) { if (errno==EINTR) continue;break; }
        if (ready>0 && (pfd.revents&POLLIN)) {
            if (used+1>=sizeof(output)) { overflow=1;break; }
            got=read(pipefd[0],output+used,sizeof(output)-1-used);
            if (got>0) { used+=(size_t)got;continue; }
            if (got==0) break;
            if (errno==EINTR) continue;
            break;
        }
        if (ready>0 && (pfd.revents&(POLLHUP|POLLERR))) break;
        {
            long long now=now_ms();
            if (now<0 || now-began>=WR_VPN_ACTION_TIMEOUT_MS) { timeout=1;break; }
        }
    }
    output[used]=0;
    if (timeout || overflow) {
        kill(child,SIGKILL);
        while (waitpid(child,&status,0)<0 && errno==EINTR) {}
        close(pipefd[0]);
        if (run_dns_sync()) append_dns_sync_failure(output,sizeof(output),&used);
        write_state(WR_VPN_ACTION_ROOT,id,overflow?"overflow":"timeout",-1,output);
        return 1;
    }
    while (waitpid(child,&status,0)<0 && errno==EINTR) {}
    close(pipefd[0]);
    code=WIFEXITED(status)?WEXITSTATUS(status):-1;
    if (run_dns_sync()) {
        append_dns_sync_failure(output,sizeof(output),&used);
        if (!code) code=12;
    }
    write_state(WR_VPN_ACTION_ROOT,id,code==0?"done":"failed",code,output);
    return code==0?0:1;
}
