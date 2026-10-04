#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <string.h>
/* Stand-in executable only; no driver access. */
int main(int argc, char **argv) {
    sigset_t mask;
    if (argc!=4 || strcmp(argv[0],"wr-band-steering") || strcmp(argv[1],"--foreground")) return 3;
    if (strcmp(argv[2],"ra0") || strcmp(argv[3],"rai0")) return 4;
    if (sigprocmask(SIG_SETMASK,0,&mask) || sigismember(&mask,SIGTERM) || sigismember(&mask,SIGCHLD)) return 5;
    if (fcntl(7,F_GETFD)!=-1 || errno!=EBADF) return 6;
    return 0;
}
