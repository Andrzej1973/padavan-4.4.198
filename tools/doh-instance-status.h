/* Bounded read-only ownership observation; does not establish DNS/TLS health. */
#ifndef WR_DOH_INSTANCE_STATUS_H
#define WR_DOH_INSTANCE_STATUS_H
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
struct wr_doh_instances {unsigned configured, owned, unknown, duplicate;};
static inline long wr_doh_owned_pid(const char *pidroot,const char *procroot,unsigned slot)
{
 char path[512],text[17],exe[128];struct stat st;int fd,error;ssize_t count;unsigned long pid=0;size_t i;
 if(slot>3)return -1;
 if(snprintf(path,sizeof(path),"%s/%u.pid",pidroot,slot)>=(int)sizeof(path))return -1;
 fd=open(path,O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);
 if(fd<0)return errno==ENOENT?0:-1;
 if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<1||st.st_size>16){close(fd);return -1;}
 count=read(fd,text,sizeof(text));error=close(fd);
 if(error||count<1||count>16||count!=st.st_size)return -1;
 if(text[count-1]=='\n')count--;
 if(!count)return -1;
 for(i=0;i<(size_t)count;i++){
  if(text[i]<'0'||text[i]>'9')return -1;
  if(pid>((unsigned long)INT_MAX-(unsigned)(text[i]-'0'))/10)return -1;
  pid=pid*10+(unsigned)(text[i]-'0');
 }
 if(pid<2)return -1;
 if(snprintf(path,sizeof(path),"%s/%lu/exe",procroot,pid)>=(int)sizeof(path))return -1;
 count=readlink(path,exe,sizeof(exe)-1);
 if(count<0)return errno==ENOENT?0:-1;
 if(count==(ssize_t)sizeof(exe)-1)return -1;
 exe[count]=0;
 return !strcmp(exe,"/usr/sbin/https_dns_proxy")?(long)pid:0;
}
static inline struct wr_doh_instances wr_doh_observe(unsigned configured,const char *pidroot,const char *procroot)
{
 struct wr_doh_instances result;long seen[4]={0,0,0,0};unsigned i,j;struct stat proc;
 memset(&result,0,sizeof(result));result.configured=configured&15U;
 if(stat(procroot,&proc)||!S_ISDIR(proc.st_mode)){result.unknown=15;return result;}
 for(i=0;i<4;i++){
  long pid=wr_doh_owned_pid(pidroot,procroot,i);
  if(pid<0){result.unknown|=1U<<i;continue;}
  if(!pid)continue;
  for(j=0;j<i;j++)if(seen[j]==pid)break;
  if(j<i){result.duplicate|=1U<<i;result.unknown|=1U<<i;continue;}
  seen[i]=pid;result.owned|=1U<<i;
 }
 return result;
}
#endif
