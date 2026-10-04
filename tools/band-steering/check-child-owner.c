#define _POSIX_C_SOURCE 200809L
#include "child-owner.h"
#include <assert.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>
static volatile sig_atomic_t stop;
static void requested(int sig) { (void)sig; stop=1; }
static void reaper(int sig) { int saved=errno; (void)sig; while(waitpid(-1,0,WNOHANG)>0) {} errno=saved; }
static pid_t child(int mode) {
    int pipefd[2]; char ready; pid_t pid; struct sigaction a; sigset_t blocked, previous;
    assert(!pipe(pipefd)); pid=fork(); assert(pid>=0);
    if (!pid) {
        sigemptyset(&blocked); sigaddset(&blocked,SIGTERM);
        assert(!sigprocmask(SIG_BLOCK,&blocked,&previous));
        close(pipefd[0]); a=(struct sigaction){0}; sigemptyset(&a.sa_mask);
        a.sa_handler=mode==2 ? SIG_IGN : requested; assert(!sigaction(SIGTERM,&a,0));
        assert(write(pipefd[1],"R",1)==1); close(pipefd[1]);
        while(!stop) { sigsuspend(&previous); }
        _exit(mode==1 ? 1 : 0);
    }
    close(pipefd[1]); assert(read(pipefd[0],&ready,1)==1); close(pipefd[0]); return pid;
}
int main(void) {
    struct sigaction a={0}; sigset_t before, after, blocked; int status;
    pid_t pid=child(0); assert(!wr_band_child_stop(&pid,1000) && pid==0);
    sigemptyset(&blocked); sigaddset(&blocked,SIGCHLD);
    assert(!sigprocmask(SIG_BLOCK,&blocked,&before));
    pid=child(0); assert(!wr_band_child_track(pid));
    assert(!kill(pid,SIGTERM)); assert(waitpid(pid,&status,0)==pid);
    wr_band_child_reaped(pid,status);
    assert(!sigprocmask(SIG_SETMASK,&before,0));
    assert(!wr_band_child_stop(&pid,1000) && pid==0);
    a.sa_handler=reaper; sigemptyset(&a.sa_mask); assert(!sigaction(SIGCHLD,&a,0));
    assert(!sigprocmask(SIG_SETMASK,0,&before));
    pid=child(0); assert(!wr_band_child_stop(&pid,1000) && pid==0);
    assert(!sigprocmask(SIG_SETMASK,0,&after));
    assert(sigismember(&before,SIGCHLD)==sigismember(&after,SIGCHLD));
    a.sa_handler=SIG_DFL; assert(!sigaction(SIGCHLD,&a,0));
    pid=child(1); assert(wr_band_child_stop(&pid,1000)==-1 && errno==EIO && pid==0);
    pid=child(2); assert(wr_band_child_stop(&pid,50)==-1 && errno==ETIMEDOUT && pid>1);
    assert(!kill(pid,SIGKILL)); assert(waitpid(pid,0,0)==pid);
    assert(wr_band_child_stop(&pid,50)==-1 && errno==ECHILD);
    pid=0; assert(wr_band_child_stop(&pid,50)==-1 && errno==EINVAL);
    assert(wr_band_child_spawn(&pid,"ra0","ra0")==-1 && pid==0);
    assert(wr_band_child_spawn(&pid,"ra0;bad","rai0")==-1 && pid==0);
    puts("PASS owned child normal/error exit, timeout preserves ownership, missing child unverified"); return 0;
}
