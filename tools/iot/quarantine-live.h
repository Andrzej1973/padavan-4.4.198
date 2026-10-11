/* Read-only kernel quarantine observation. Caller owns the service guard.
 * Fixed argv, no shell, bounded output/deadline; neither applies firewall rules
 * nor proves that hardware offload is disabled. */
#ifndef WR_IOT_QUARANTINE_LIVE_H
#define WR_IOT_QUARANTINE_LIVE_H
#include "quarantine-check.h"
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <time.h>
#include <errno.h>
#include <sys/wait.h>
#include <dirent.h>
static inline long long wr_iot_quarantine_clock(void){
 struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return -1;
 return (long long)t.tv_sec*1000+t.tv_nsec/1000000;
}
static inline int wr_iot_quarantine_live(int ipv6){
 const size_t limit=256U*1024U;char *data;int pipes[2],status=0,exited=0,eof=0,ok=0;
 pid_t child;size_t used=0;long long start,now;
 const char *path=ipv6?"/bin/ip6tables-save":"/bin/iptables-save";
 if(ipv6!=0&&ipv6!=1)return 0;
 start=wr_iot_quarantine_clock();if(start<0)return 0;
 data=malloc(limit+1);if(!data)return 0;
 if(pipe(pipes)){free(data);return 0;}
 if(fcntl(pipes[0],F_SETFL,O_NONBLOCK)<0){close(pipes[0]);close(pipes[1]);free(data);return 0;}
 child=fork();
 if(child==0){
  DIR *directory;struct dirent *entry;int nullfd;
  char *const argv[]={(char *)path,"-t","filter",NULL};
  char *const environment[]={"PATH=/bin:/usr/bin:/sbin:/usr/sbin","LC_ALL=C",NULL};
  if(dup2(pipes[1],STDOUT_FILENO)<0)_exit(127);
  nullfd=open("/dev/null",O_RDWR);
  if(nullfd<0||dup2(nullfd,STDIN_FILENO)<0||dup2(nullfd,STDERR_FILENO)<0)_exit(127);
  /* Do not let the observation command inherit service locks or snapshots. */
  directory=opendir("/proc/self/fd");if(!directory)_exit(127);
  while((entry=readdir(directory))){
   char *end;long fd=strtol(entry->d_name,&end,10);
   if(!*end&&fd>2&&fd!=dirfd(directory))close((int)fd);
  }
  closedir(directory);execve(path,argv,environment);_exit(127);
 }
 close(pipes[1]);
 if(child<0){close(pipes[0]);free(data);return 0;}
 while(1){
  struct pollfd ready={pipes[0],POLLIN,0};ssize_t n;pid_t result;
  now=wr_iot_quarantine_clock();if(now<0||now-start>=3000)break;
  if(!eof){
   n=read(pipes[0],data+used,limit+1-used);
   if(n>0){used+=(size_t)n;if(used>limit)break;}
   else if(!n)eof=1;
   else if(errno!=EAGAIN&&errno!=EWOULDBLOCK&&errno!=EINTR)break;
  }
  if(!exited){
   result=waitpid(child,&status,WNOHANG);
   if(result==child)exited=1;
   else if(result<0&&errno!=EINTR){if(errno==ECHILD)exited=1;break;}
  }
  if(exited&&eof){ok=WIFEXITED(status)&&WEXITSTATUS(status)==0&&wr_iot_quarantine_snapshot(data,used);break;}
  if(eof)ready.fd=-1;
  if(poll(&ready,1,20)<0&&errno!=EINTR)break;
 }
 if(!exited){kill(child,SIGKILL);while(waitpid(child,&status,0)<0&&errno==EINTR){} }
 close(pipes[0]);free(data);return ok;
}
#endif
