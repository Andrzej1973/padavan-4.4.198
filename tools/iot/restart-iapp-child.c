#define _GNU_SOURCE
#include <unistd.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>
#include "restart-iapp-child.h"
#ifndef WR_IOT_IAPP_SCRIPT
#define WR_IOT_IAPP_SCRIPT "/usr/bin/iappd.sh"
#endif
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*s)
{
 int pipes[2];pid_t supervisor;
 if(!s||s->owner||s->attempted)return 0;
 if(pipe2(pipes,O_CLOEXEC|O_NONBLOCK))return 0;
 s->owner=getpid();s->attempted=1;s->fd=pipes[0];
 supervisor=fork();
 if(supervisor<0){close(pipes[0]);close(pipes[1]);s->fd=-1;s->result=-1;return 0;}
 if(!supervisor){
  struct sigaction action={0};sigset_t empty;pid_t command;int status;unsigned char receipt=2;
  close(pipes[0]);
  /* Supervisor owns its command status; PID1's inherited handler must not reap it. */
  action.sa_handler=SIG_DFL;sigemptyset(&action.sa_mask);
  if(sigaction(SIGCHLD,&action,NULL))goto report;
  command=fork();
  if(command==0){
   int sig,fd;long limit=sysconf(_SC_OPEN_MAX);close(pipes[1]);
   if(limit<0||limit>1048576)_exit(126);
   for(fd=3;fd<limit;fd++)close(fd);
   for(sig=1;sig<_NSIG;sig++)if(sig!=SIGKILL&&sig!=SIGSTOP)(void)sigaction(sig,&action,NULL);
   sigemptyset(&empty);if(sigprocmask(SIG_SETMASK,&empty,NULL))_exit(126);
   execl(WR_IOT_IAPP_SCRIPT,WR_IOT_IAPP_SCRIPT,"restart",(char*)0);_exit(127);
  }
  if(command>0){
   pid_t done;do{done=waitpid(command,&status,0);}while(done<0&&errno==EINTR);
   if(done==command&&WIFEXITED(status)&&WEXITSTATUS(status)==0)receipt=1;
  }
  report:{ssize_t sent;do{sent=write(pipes[1],&receipt,1);}while(sent<0&&errno==EINTR);
   close(pipes[1]);_exit(sent==1?0:1);}
 }
 close(pipes[1]);return 1;
}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s)
{
 unsigned char receipt;ssize_t count;
 if(!s||s->owner!=getpid()||!s->attempted)return -1;
 if(s->result)return s->result;
 if(s->fd<0)return -1;
 count=read(s->fd,&receipt,1);
 if(count<0&&(errno==EAGAIN||errno==EWOULDBLOCK||errno==EINTR))return 0;
 s->result=count==1&&receipt==1?1:-1;
 if(close(s->fd))s->result=-1;
 s->fd=-1;return s->result;
}
