#ifndef WR_ACTION_CHANNEL_H
#define WR_ACTION_CHANNEL_H
#include "action-send.h"
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>
struct wr_action_channel {int fd;uint64_t retry_at;dev_t device;ino_t inode;};
static inline void wr_action_channel_init(struct wr_action_channel *c){memset(c,0,sizeof(*c));c->fd=-1;}
static inline void wr_action_channel_close(struct wr_action_channel *c){if(c->fd>=0)close(c->fd);c->fd=-1;c->inode=0;}
/* Caller supplies a fixed local endpoint, never a value from HTTP input.
 * Retry no faster than 10 seconds. Failed reports are counted by reporter. */
static inline int wr_action_channel_emit(struct wr_action_channel *c,const char *path,uint64_t now,const struct wr_action_event *e){
 struct stat st,before;struct sockaddr_un addr;char parent[108],*slash;size_t n;int saved=errno,ok=0;
 if(!c||!path||!wr_action_valid(e))goto done;
 n=strnlen(path,sizeof(addr.sun_path));if(!n||n>=sizeof(addr.sun_path)||path[0]!='/')goto done;
 if(c->fd>=0&&(lstat(path,&st)||!S_ISSOCK(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&0777)!=0600||st.st_dev!=c->device||st.st_ino!=c->inode))wr_action_channel_close(c);
 if(c->fd<0){
  if(now<c->retry_at)goto done;
  c->retry_at=now>UINT64_MAX-10000?UINT64_MAX:now+10000;
  memcpy(parent,path,n+1);slash=strrchr(parent,'/');if(!slash||slash==parent)goto done;*slash=0;
  if(lstat(parent,&st)||!S_ISDIR(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&0777)!=0700)goto done;
  if(lstat(path,&before)||!S_ISSOCK(before.st_mode)||before.st_uid!=geteuid()||(before.st_mode&0777)!=0600||before.st_nlink!=1)goto done;
  c->fd=socket(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);if(c->fd<0)goto done;
  memset(&addr,0,sizeof(addr));addr.sun_family=AF_UNIX;memcpy(addr.sun_path,path,n+1);
  if(connect(c->fd,(struct sockaddr *)&addr,(socklen_t)(offsetof(struct sockaddr_un,sun_path)+n+1))||lstat(path,&st)||st.st_dev!=before.st_dev||st.st_ino!=before.st_ino){wr_action_channel_close(c);goto done;}
  c->device=st.st_dev;c->inode=st.st_ino;
 }
 ok=wr_action_send(c->fd,e);if(!ok)wr_action_channel_close(c);
done:errno=saved;return ok;
}
#endif
