#ifndef WR_USBIP_JOB_WORKER_H
#define WR_USBIP_JOB_WORKER_H
/* Candidate asynchronous executor. Not wired into HTTPD yet. */
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#ifndef WR_USBIP_CONTROLLER
#define WR_USBIP_CONTROLLER "/usr/sbin/wr-usbip"
#endif
struct wr_usbip_job_result {
 char id[33];unsigned state;unsigned long long started,observed;int code;
};
/* Reap only the tracked worker; never consume another HTTP utility's child. */
static int wr_usbip_job_reap(pid_t *worker)
{
 int status;pid_t result;
 if(!worker||*worker<=0)return 1;
 do{result=waitpid(*worker,&status,WNOHANG);}while(result<0&&errno==EINTR);
 if(result==*worker||(result<0&&errno==ECHILD)){*worker=0;return 1;}
 return 0;
}
static int wr_usbip_job_args(const char *action,const char *bus,const char *vendor,const char *product)
{
 const char *p;size_t i;
 if(!action||!bus||!vendor||!product||(strcmp(action,"bind")&&strcmp(action,"unbind")))return 0;
 if(strlen(bus)>31||!isdigit((unsigned char)*bus))return 0;
 p=bus;while(isdigit((unsigned char)*p))p++;
 if(*p++!='-'||!isdigit((unsigned char)*p))return 0;
 for(;;){while(isdigit((unsigned char)*p))p++;if(!*p)break;if(*p++!='.'||!isdigit((unsigned char)*p))return 0;}
 if(strlen(vendor)!=4||strlen(product)!=4)return 0;
 for(i=0;i<4;i++)if(!isxdigit((unsigned char)vendor[i])||!isxdigit((unsigned char)product[i]))return 0;
 return 1;
}
static unsigned long long wr_usbip_job_now(void)
{
 struct timespec ts;
 if(clock_gettime(CLOCK_MONOTONIC,&ts))return 0;
 return (unsigned long long)ts.tv_sec;
}
static int wr_usbip_job_close_fds(int keep)
{
 DIR *dir=opendir("/proc/self/fd");struct dirent *entry;unsigned n=0;int ok=1;
 if(!dir)return 0;
 for(;;){char *end;long fd;errno=0;entry=readdir(dir);if(!entry){if(errno)ok=0;break;}
  if(++n>1024){ok=0;break;}
  errno=0;fd=strtol(entry->d_name,&end,10);
  if(!errno&&!*end&&fd>2&&fd<=INT_MAX&&fd!=keep&&fd!=dirfd(dir))close((int)fd);
 }
 if(closedir(dir))ok=0;
 return ok;
}
/* 1 running, 2 controller success, 3 failure/unconfirmed. Never a USB transfer claim. */
static int wr_usbip_job_publish(const char *dir,const char *id,unsigned state,unsigned long long started,int code)
{
 char temporary[PATH_MAX],target[PATH_MAX],body[256];int fd,n,ok;
 if(snprintf(temporary,sizeof(temporary),"%s/.%s.tmp",dir,id)>=(int)sizeof(temporary)||
    snprintf(target,sizeof(target),"%s/result",dir)>=(int)sizeof(target))return 0;
 fd=open(temporary,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);if(fd<0)return 0;
 n=snprintf(body,sizeof(body),"{\"id\":\"%s\",\"state\":%u,\"started\":%llu,\"observed\":%llu,\"code\":%d}\n",
  id,state,started,wr_usbip_job_now(),code);
 ok=n>0&&n<(int)sizeof(body)&&write(fd,body,(size_t)n)==n;
 if(close(fd))ok=0;
 if(ok&&rename(temporary,target)==0)return 1;
 unlink(temporary);return 0;
}
/* Unknown/missing/stale/mismatched results return zero with a cleared output. */
static int wr_usbip_job_read(const char *dir,const char *requested,unsigned long long now,
 unsigned long long max_age,struct wr_usbip_job_result *out)
{
 struct stat st;struct wr_usbip_job_result value;
 char path[PATH_MAX],body[256],canonical[256];int fd,used=0,n;ssize_t length;
 if(!out)return 0;
 memset(out,0,sizeof(*out));memset(&value,0,sizeof(value));
 if(!dir||!requested||strlen(requested)!=32||strspn(requested,"0123456789abcdef")!=32||!now||!max_age)return 0;
 if(lstat(dir,&st)||!S_ISDIR(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&077))return 0;
 if(snprintf(path,sizeof(path),"%s/result",dir)>=(int)sizeof(path))return 0;
 fd=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK);if(fd<0)return 0;
 if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||st.st_nlink!=1||
    (st.st_mode&077)||st.st_size<=0||st.st_size>=(off_t)sizeof(body)){close(fd);return 0;}
 length=read(fd,body,sizeof(body)-1);close(fd);
 if(length!=st.st_size)return 0;
 body[length]=0;if(strlen(body)!=(size_t)length)return 0;
 errno=0;
 n=sscanf(body,"{\"id\":\"%32[0123456789abcdef]\",\"state\":%1u,\"started\":%20llu,\"observed\":%20llu,\"code\":%4d}\n%n",
  value.id,&value.state,&value.started,&value.observed,&value.code,&used);
 if(errno||n!=5||used!=length||strcmp(value.id,requested))return 0;
 n=snprintf(canonical,sizeof(canonical),"{\"id\":\"%s\",\"state\":%u,\"started\":%llu,\"observed\":%llu,\"code\":%d}\n",
  value.id,value.state,value.started,value.observed,value.code);
 if(n!=length||strcmp(canonical,body)||value.state<1||value.state>3||!value.started||
    value.observed<value.started||now<value.observed||now-value.observed>max_age||
    (value.state==1&&(value.code!=-1||now-value.started>max_age))||
    (value.state==2&&value.code!=0)||
    (value.state==3&&(value.code==0||value.code< -1||value.code>255)))return 0;
 *out=value;return 1;
}
/* Caller must reap returned child without waiting in its HTTP request loop.
 * A stuck kernel operation keeps the job lock; no new operation is admitted.
 * UI must treat old running results as unconfirmed, not as success or stopped. */
static int wr_usbip_job_start_serial(const char *dir,const char *action,const char *bus,
 const char *vendor,const char *product,const char *serial,char id[33],pid_t *worker)
{
 char lockpath[PATH_MAX];unsigned char random[16];struct stat st;
 int lockfd,randomfd,i;pid_t child;unsigned long long started;
 if(!dir||!id||!worker||!wr_usbip_job_args(action,bus,vendor,product))return 0;
 if(serial && *serial){
  size_t n=strlen(serial),j;
  if(n>512 || n%2)return 0;
  for(j=0;j<n;j++)if(!strchr("0123456789abcdef",serial[j]))return 0;
 }
 if(mkdir(dir,0700)&&errno!=EEXIST)return 0;
 if(lstat(dir,&st)||!S_ISDIR(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&077))return 0;
 if(snprintf(lockpath,sizeof(lockpath),"%s/lock",dir)>=(int)sizeof(lockpath))return 0;
 lockfd=open(lockpath,O_RDWR|O_CREAT|O_NOFOLLOW,0600);if(lockfd<0)return 0;
 if(lockfd<3){int moved=fcntl(lockfd,F_DUPFD,3);close(lockfd);lockfd=moved;if(lockfd<0)return 0;}
 if(fstat(lockfd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||st.st_nlink!=1||
    (st.st_mode&077)||flock(lockfd,LOCK_EX|LOCK_NB)){close(lockfd);return 0;}
 randomfd=open("/dev/urandom",O_RDONLY);
 if(randomfd<0){close(lockfd);return 0;}
 {ssize_t got=read(randomfd,random,sizeof(random));close(randomfd);if(got!=(ssize_t)sizeof(random)){close(lockfd);return 0;}}
 for(i=0;i<16;i++)snprintf(id+i*2,3,"%02x",random[i]);
 started=wr_usbip_job_now();
 if(!started||!wr_usbip_job_publish(dir,id,1,started,-1)){close(lockfd);return 0;}
 child=fork();
 if(child<0){wr_usbip_job_publish(dir,id,3,started,-1);close(lockfd);return 0;}
 if(!child){
  int nullfd,status=0,code=-1;pid_t command,waited;
  signal(SIGCHLD,SIG_DFL);signal(SIGPIPE,SIG_DFL);signal(SIGTERM,SIG_DFL);
  if(setsid()<0)goto failed;
  nullfd=open("/dev/null",O_RDWR);if(nullfd<0)goto failed;
  if(dup2(nullfd,0)<0||dup2(nullfd,1)<0||dup2(nullfd,2)<0)goto failed;
  if(!wr_usbip_job_close_fds(lockfd))goto failed;
  command=fork();if(command<0)goto failed;
  if(!command){
   close(lockfd);
   if(serial && *serial)
    execl(WR_USBIP_CONTROLLER,WR_USBIP_CONTROLLER,action,bus,vendor,product,serial,(char *)NULL);
   else
    execl(WR_USBIP_CONTROLLER,WR_USBIP_CONTROLLER,action,bus,vendor,product,(char *)NULL);
   _exit(127);
  }
  do{waited=waitpid(command,&status,0);}while(waited<0&&errno==EINTR);
  if(waited==command&&WIFEXITED(status))code=WEXITSTATUS(status);
  wr_usbip_job_publish(dir,id,code==0?2:3,started,code);
  close(lockfd);_exit(0);
 failed:
  wr_usbip_job_publish(dir,id,3,started,-1);close(lockfd);_exit(1);
 }
 *worker=child;close(lockfd);return 1;
}
static inline int wr_usbip_job_start(const char *dir,const char *action,const char *bus,
 const char *vendor,const char *product,char id[33],pid_t *worker)
{
 return wr_usbip_job_start_serial(dir,action,bus,vendor,product,NULL,id,worker);
}
#endif
