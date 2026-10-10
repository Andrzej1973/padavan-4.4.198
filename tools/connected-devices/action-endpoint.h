#ifndef WR_ACTION_ENDPOINT_H
#define WR_ACTION_ENDPOINT_H
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <sys/file.h>
#include <fcntl.h>
#include <stddef.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
struct wr_action_endpoint {int fd,lock_fd;dev_t device;ino_t inode;char path[108];};
static inline void wr_action_endpoint_close(struct wr_action_endpoint *e){
 struct stat st;
 if(!e)return;
 if(e->fd>=0)close(e->fd);
 if(e->inode&&!lstat(e->path,&st)&&S_ISSOCK(st.st_mode)&&st.st_uid==geteuid()&&st.st_dev==e->device&&st.st_ino==e->inode)unlink(e->path);
 if(e->lock_fd>=0)close(e->lock_fd);
 e->fd=e->lock_fd=-1;e->inode=0;
}
/* All endpoint owners must retain this same persistent lock inode. Never
 * unlink the lock file. The private parent must already exist and be owned. */
static inline int wr_action_endpoint_open(struct wr_action_endpoint *e,const char *path){
 struct stat st;struct sockaddr_un address;char parent[108],lock[114],*slash;size_t n;int one=1,saved;
 if(!e||!path)return -1;
 memset(e,0,sizeof(*e));e->fd=e->lock_fd=-1;
 n=strnlen(path,108);if(!n||n>=108||path[0]!='/'){errno=EINVAL;return -1;}
 memcpy(parent,path,n+1);slash=strrchr(parent,'/');if(!slash||slash==parent||!slash[1]){errno=EINVAL;return -1;}*slash=0;
 if(lstat(parent,&st)||!S_ISDIR(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&0777)!=0700){errno=EPERM;return -1;}
 memcpy(lock,path,n);memcpy(lock+n,".lock",6);
 e->lock_fd=open(lock,O_RDWR|O_CREAT|O_CLOEXEC|O_NOFOLLOW,0600);if(e->lock_fd<0)return -1;
 if(fstat(e->lock_fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||st.st_nlink!=1||(st.st_mode&0777)!=0600){errno=EPERM;goto fail;}
 if(flock(e->lock_fd,LOCK_EX|LOCK_NB))goto fail;
 if(!lstat(path,&st)){
  if(!S_ISSOCK(st.st_mode)||st.st_uid!=geteuid()||st.st_nlink!=1||(st.st_mode&0777)!=0600){errno=EPERM;goto fail;}
  if(unlink(path))goto fail;
 }else if(errno!=ENOENT)goto fail;
 e->fd=socket(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);if(e->fd<0)goto fail;
 memset(&address,0,sizeof(address));address.sun_family=AF_UNIX;memcpy(address.sun_path,path,n+1);memcpy(e->path,path,n+1);
 if(setsockopt(e->fd,SOL_SOCKET,SO_PASSCRED,&one,sizeof(one))||bind(e->fd,(struct sockaddr *)&address,(socklen_t)(offsetof(struct sockaddr_un,sun_path)+n+1)))goto fail;
 if(lstat(path,&st))goto fail;
 e->device=st.st_dev;e->inode=st.st_ino;
 if(chmod(path,0600))goto fail;
 return 0;
fail:saved=errno;wr_action_endpoint_close(e);errno=saved;return -1;
}
#endif
