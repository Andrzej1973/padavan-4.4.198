#ifndef WR_EOIP_RUNTIME_STATE_H
#define WR_EOIP_RUNTIME_STATE_H
/* Volatile recovery identity, separate from persistent requested profiles. */
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
struct wr_eoip_state {int fd;char directory[PATH_MAX];};
static int wr_eoip_state_lock(const char *directory,struct wr_eoip_state *state)
{
 struct stat st;char path[PATH_MAX];int fd;
 if(!directory||!state||state->fd>=0||strlen(directory)>=sizeof(state->directory))return 0;
 if(mkdir(directory,0700)&&errno!=EEXIST)return 0;
 if(lstat(directory,&st)||!S_ISDIR(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&077))return 0;
 if(snprintf(path,sizeof(path),"%s/lock",directory)>=(int)sizeof(path))return 0;
 fd=open(path,O_RDWR|O_CREAT|O_NOFOLLOW,0600);if(fd<0)return 0;
 if(fcntl(fd,F_SETFD,FD_CLOEXEC)||fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||
    st.st_nlink!=1||(st.st_mode&077)||flock(fd,LOCK_EX|LOCK_NB)){close(fd);return 0;}
 strcpy(state->directory,directory);state->fd=fd;return 1;
}
static void wr_eoip_state_unlock(struct wr_eoip_state *state)
{
 if(state&&state->fd>=0){close(state->fd);state->fd=-1;state->directory[0]=0;}
}
static int wr_eoip_state_path(struct wr_eoip_state *state,unsigned slot,char path[PATH_MAX])
{
 return state&&state->fd>=0&&slot<8&&snprintf(path,PATH_MAX,"%s/%u",state->directory,slot)<PATH_MAX;
}
/* 0 unknown/corrupt, 1 absent, 2 valid recorded ifindex. Caller holds lock. */
static int wr_eoip_state_read(struct wr_eoip_state *state,unsigned slot,unsigned *index)
{
 char path[PATH_MAX],body[32],canonical[32],*end;struct stat st;int fd,n;ssize_t length;unsigned long value;
 if(!index)return 0;
 *index=0;if(!wr_eoip_state_path(state,slot,path))return 0;
 fd=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK);if(fd<0)return errno==ENOENT?1:0;
 if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||st.st_nlink!=1||
    (st.st_mode&077)||st.st_size<5||st.st_size>=(off_t)sizeof(body)){close(fd);return 0;}
 length=read(fd,body,sizeof(body)-1);close(fd);if(length!=st.st_size)return 0;
 body[length]=0;if(strlen(body)!=(size_t)length||strncmp(body,"v1 ",3)||body[3]<'0'||body[3]>'9')return 0;
 errno=0;value=strtoul(body+3,&end,10);
 if(errno||value==0||value>INT_MAX||strcmp(end,"\n"))return 0;
 n=snprintf(canonical,sizeof(canonical),"v1 %lu\n",value);
 if(n!=length||strcmp(body,canonical))return 0;
 *index=(unsigned)value;return 2;
}
static int wr_eoip_state_write(struct wr_eoip_state *state,unsigned slot,unsigned index)
{
 char path[PATH_MAX],temporary[PATH_MAX],body[32];unsigned prior;int read_state,fd,n,ok;
 if(!index||index>INT_MAX||!wr_eoip_state_path(state,slot,path))return 0;
 read_state=wr_eoip_state_read(state,slot,&prior);
 if(read_state==0||(read_state==2&&prior!=index))return 0;
 if(snprintf(temporary,sizeof(temporary),"%s/.%u.%ld.tmp",state->directory,slot,(long)getpid())>=(int)sizeof(temporary))return 0;
 fd=open(temporary,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);if(fd<0)return 0;
 n=snprintf(body,sizeof(body),"v1 %u\n",index);ok=n>0&&write(fd,body,(size_t)n)==n;
 if(close(fd))ok=0;
 if(ok&&rename(temporary,path)==0)return 1;
 unlink(temporary);return 0;
}
static int wr_eoip_state_clear(struct wr_eoip_state *state,unsigned slot,unsigned expected)
{
 char path[PATH_MAX];unsigned index;int result;
 if(!expected||!wr_eoip_state_path(state,slot,path))return 0;
 result=wr_eoip_state_read(state,slot,&index);
 if(result==1)return 1;
 if(result!=2||index!=expected)return 0;
 return unlink(path)==0;
}
#endif
