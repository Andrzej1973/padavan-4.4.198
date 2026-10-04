#define _POSIX_C_SOURCE 200809L
#include "child-owner.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>
int main(void) {
    pid_t pid=0; int fd,status; sigset_t blocked,previous,after;
    fd=open("/dev/null",O_RDONLY); assert(fd>=0); assert(dup2(fd,7)==7);
    sigemptyset(&blocked); sigaddset(&blocked,SIGTERM);
    assert(!sigprocmask(SIG_BLOCK,&blocked,&previous));
    assert(!wr_band_child_spawn(&pid,"ra0","rai0") && pid>1);
    assert(!sigprocmask(SIG_SETMASK,0,&after) && sigismember(&after,SIGTERM)==1);
    assert(waitpid(pid,&status,0)==pid && WIFEXITED(status) && !WEXITSTATUS(status));
    wr_band_child_reaped(pid,status); assert(!wr_band_child_stop(&pid,1000) && pid==0);
    assert(!wr_band_child_spawn(&pid,"ra1","rai0"));
    assert(waitpid(pid,&status,0)==pid && WIFEXITED(status) && WEXITSTATUS(status)==4);
    wr_band_child_reaped(pid,status); assert(wr_band_child_stop(&pid,1000)==-1 && errno==EIO && !pid);
    assert(!sigprocmask(SIG_SETMASK,&previous,0)); close(fd); close(7);
    puts("PASS actual fork/exec arguments, mask restoration, FD closure and reaped status; daemon readiness unverified");
    return 0;
}
