#ifndef WR_HANDSHAKE_WORKER_H
#define WR_HANDSHAKE_WORKER_H
#include "handshake-observation.h"
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <errno.h>
#include <dirent.h>
#include <stdlib.h>
#include <limits.h>
#ifndef WR_HANDSHAKE_TOOL
#define WR_HANDSHAKE_TOOL "/usr/bin/wg"
#endif
/* Release inherited HTTP sockets/IPC; retain only stdio and one result pipe. */
static inline int wr_handshake_close_extra_fds(int keep)
{
 DIR *fds;struct dirent *entry;unsigned count=0;int ok=1;
 fds=opendir("/proc/self/fd");if(!fds)return 0;
 for(;;){
  char *end;long fd;
  errno=0;entry=readdir(fds);
  if(!entry){if(errno)ok=0;break;}
  if(++count>1024){ok=0;break;}
  errno=0;fd=strtol(entry->d_name,&end,10);
  if(!errno && !*end && fd>2 && fd<=INT_MAX && fd!=keep && fd!=dirfd(fds))close((int)fd);
 }
 if(closedir(fds))ok=0;
 return ok;
}
/* Only invoke in a supervised worker, never synchronously in the HTTP loop.
 * Supervisor must bound runtime and kill/reap the worker process group. */
static inline int wr_handshake_worker_query(const char *interface,uint64_t now,
 struct wr_handshake_observation *out)
{
 int pipes[2],status,ok;pid_t child,waited;FILE *fp;
 struct wr_handshake_observation candidate;
 if(!interface||!out||(strcmp(interface,"wg0")&&strcmp(interface,"wg1")))return 0;
 if(pipe(pipes))return 0;
 child=fork();
 if(child<0){close(pipes[0]);close(pipes[1]);return 0;}
 if(!child){
  int nullfd;
  signal(SIGPIPE,SIG_DFL);signal(SIGCHLD,SIG_DFL);signal(SIGTERM,SIG_DFL);
  close(pipes[0]);
  if(dup2(pipes[1],STDOUT_FILENO)<0)_exit(126);
  nullfd=open("/dev/null",O_RDWR);if(nullfd<0)_exit(126);
  if(dup2(nullfd,STDIN_FILENO)<0||dup2(nullfd,STDERR_FILENO)<0)_exit(126);
  /* Do not let the utility retain HTTP listeners, client sockets or IPC. */
  if(!wr_handshake_close_extra_fds(-1))_exit(126);
  execl(WR_HANDSHAKE_TOOL,WR_HANDSHAKE_TOOL,"show",interface,"latest-handshakes",(char *)NULL);
  _exit(127);
 }
 close(pipes[1]);fp=fdopen(pipes[0],"r");
 if(!fp){close(pipes[0]);kill(child,SIGKILL);do{waited=waitpid(child,&status,0);}while(waited<0&&errno==EINTR);return 0;}
 ok=wr_handshake_read(fp,now,300,&candidate);
 if(fclose(fp))ok=0;
 if(!ok)kill(child,SIGKILL);
 do{waited=waitpid(child,&status,0);}while(waited<0&&errno==EINTR);
 if(waited!=child||!WIFEXITED(status)||WEXITSTATUS(status)!=0)ok=0;
 if(ok)*out=candidate;
 return ok;
}
#endif
