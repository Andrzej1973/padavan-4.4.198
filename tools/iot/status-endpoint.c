#define _GNU_SOURCE
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <poll.h>
#include <time.h>
#include "status-endpoint.h"
#define STATUS_NAME "status.sock"
static unsigned long long endpoint_ms(void)
{struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t)||t.tv_sec<=0)return 0;return (unsigned long long)t.tv_sec*1000+(unsigned long long)t.tv_nsec/1000000;}
static int directory_current(int fd,const char *path,uid_t uid)
{
 struct stat held,named;
 return fd>=0&&!fstat(fd,&held)&&!lstat(path,&named)&&
  S_ISDIR(held.st_mode)&&S_ISDIR(named.st_mode)&&held.st_uid==uid&&
  (held.st_mode&07777)==0700&&held.st_dev==named.st_dev&&held.st_ino==named.st_ino;
}
static int socket_identity(const struct wr_iot_status_endpoint *s)
{
 struct stat named;
 return directory_current(s->directory,s->path,s->uid)&&
  !fstatat(s->directory,STATUS_NAME,&named,AT_SYMLINK_NOFOLLOW)&&
  S_ISSOCK(named.st_mode)&&named.st_uid==s->uid&&
  named.st_nlink==1&&named.st_dev==s->device&&named.st_ino==s->inode;
}
static int socket_current(const struct wr_iot_status_endpoint *s)
{
 struct stat named;
 return socket_identity(s)&&!fstatat(s->directory,STATUS_NAME,&named,AT_SYMLINK_NOFOLLOW)&&
  (named.st_mode&07777)==0600;
}
static int descriptor_current(int fd,dev_t device,ino_t inode,int directory)
{
 struct stat held;
 return fd>=0&&inode&&!fstat(fd,&held)&&held.st_dev==device&&held.st_ino==inode&&
  (directory?S_ISDIR(held.st_mode):S_ISSOCK(held.st_mode));
}
static void close_connection(struct wr_iot_status_endpoint *s)
{
 if(descriptor_current(s->connection,s->connection_device,s->connection_inode,0))close(s->connection);
 s->connection=-1;s->connection_device=0;s->connection_inode=0;s->expires=0;
}
int wr_iot_status_endpoint_ready_fd(struct wr_iot_status_endpoint *s)
{
 if(!s||s->owner!=getpid()||!socket_current(s))return -1;
 if(s->connection>=0){
  if(descriptor_current(s->connection,s->connection_device,s->connection_inode,0))return s->connection;
  close_connection(s); /* Forget, never close a replacement descriptor. */
 }
 if(descriptor_current(s->listener,s->listener_device,s->listener_inode,0))return s->listener;
 s->listener=-1;return -1;
}
void wr_iot_status_endpoint_init(struct wr_iot_status_endpoint *s)
{if(s){memset(s,0,sizeof(*s));s->directory=s->listener=s->connection=-1;}}
int wr_iot_status_endpoint_listen(struct wr_iot_status_endpoint *s,const char *path,uid_t uid)
{
 struct sockaddr_un address={.sun_family=AF_UNIX};struct stat named;int fd;
 if(!s||!path||s->owner||s->directory!=-1||s->listener!=-1||s->connection!=-1||
    geteuid()!=uid||strlen(path)>=sizeof(s->path)||
    snprintf(address.sun_path,sizeof(address.sun_path),"%s/%s",path,STATUS_NAME)>=(int)sizeof(address.sun_path))return 0;
 fd=open(path,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return 0;
 if(!directory_current(fd,path,uid)){close(fd);return 0;}
 int sock=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_NONBLOCK|SOCK_CLOEXEC,0);
 if(sock<0){close(fd);return 0;}
 if(bind(sock,(struct sockaddr *)&address,sizeof(address))){close(sock);close(fd);return 0;}
 /* The private directory is controlled by the same trusted UID. Never remove
  * a pre-existing endpoint; capture only the inode created by this bind. */
 if(fstatat(fd,STATUS_NAME,&named,AT_SYMLINK_NOFOLLOW)||!S_ISSOCK(named.st_mode)||named.st_uid!=uid){close(sock);close(fd);return 0;}
 s->owner=getpid();s->uid=uid;s->directory=fd;s->listener=sock;
 s->device=named.st_dev;s->inode=named.st_ino;strcpy(s->path,path);
 struct stat held;
 if(fstat(fd,&held)){close(sock);close(fd);wr_iot_status_endpoint_init(s);return 0;}
 s->directory_device=held.st_dev;s->directory_inode=held.st_ino;
 if(fstat(sock,&held)){close(sock);close(fd);wr_iot_status_endpoint_init(s);return 0;}
 s->listener_device=held.st_dev;s->listener_inode=held.st_ino;
 if(fchmodat(fd,STATUS_NAME,0600,0)||!socket_current(s)||listen(sock,4)){
  (void)wr_iot_status_endpoint_close(s);return 0;
 }
 return 1;
}
int wr_iot_status_endpoint_step(struct wr_iot_status_endpoint *s,int (*observe)(const struct wr_iot_control_result *))
{
 unsigned long long now;int ready,answered=0;
 if(!s||!observe||wr_iot_status_endpoint_ready_fd(s)<0)return 0;
 now=endpoint_ms();if(!now)return 0;
 if(s->connection<0){
  s->connection=accept(s->listener,NULL,NULL);if(s->connection<0)return 0;
  struct stat held;
  if(fstat(s->connection,&held)){close(s->connection);s->connection=-1;return 0;}
  s->connection_device=held.st_dev;s->connection_inode=held.st_ino;
  int flags=fcntl(s->connection,F_GETFL);
  if(flags<0||fcntl(s->connection,F_SETFL,flags|O_NONBLOCK)||fcntl(s->connection,F_SETFD,FD_CLOEXEC)){
   close_connection(s);return 0;
  }
  s->expires=now+1000;
 }
 if(now>=s->expires){close_connection(s);return 0;}
 struct pollfd p={s->connection,POLLIN,0};ready=poll(&p,1,0);
 if(ready>0)answered=wr_iot_status_serve_once(s->connection,s->uid,observe);
 if(ready!=0||now>=s->expires){close_connection(s);}
 return answered;
}
int wr_iot_status_endpoint_close(struct wr_iot_status_endpoint *s)
{
 int removed;
 if(!s||s->owner!=getpid())return 0;
 removed=socket_identity(s)&&!unlinkat(s->directory,STATUS_NAME,0);
 close_connection(s);
 if(descriptor_current(s->listener,s->listener_device,s->listener_inode,0))close(s->listener);
 if(descriptor_current(s->directory,s->directory_device,s->directory_inode,1))close(s->directory);
 wr_iot_status_endpoint_init(s);return removed;
}
int wr_iot_status_endpoint_query(const char *path,pid_t pid,uid_t uid,const struct wr_iot_control_result *r)
{
 struct sockaddr_un address={.sun_family=AF_UNIX};struct wr_iot_status_endpoint expected;
 struct stat named;int fd,sock,ok=0;
 if(!path||pid<=0||strlen(path)>=sizeof(expected.path)||
    snprintf(address.sun_path,sizeof(address.sun_path),"%s/%s",path,STATUS_NAME)>=(int)sizeof(address.sun_path))return 0;
 fd=open(path,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return 0;
 if(!directory_current(fd,path,uid)||fstatat(fd,STATUS_NAME,&named,AT_SYMLINK_NOFOLLOW)||
    !S_ISSOCK(named.st_mode)||named.st_uid!=uid||(named.st_mode&07777)!=0600||named.st_nlink!=1){close(fd);return 0;}
 wr_iot_status_endpoint_init(&expected);expected.directory=fd;expected.uid=uid;
 expected.device=named.st_dev;expected.inode=named.st_ino;strcpy(expected.path,path);
 sock=socket(AF_UNIX,SOCK_SEQPACKET|SOCK_NONBLOCK|SOCK_CLOEXEC,0);
 if(sock>=0){
  if(!connect(sock,(struct sockaddr *)&address,sizeof(address))&&socket_current(&expected))
   ok=wr_iot_status_query(sock,pid,uid,r)&&socket_current(&expected);
  close(sock);
 }
 close(fd);return ok;
}
