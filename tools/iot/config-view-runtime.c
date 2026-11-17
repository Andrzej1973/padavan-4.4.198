#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include "config-view-runtime.h"
#include "config-view-endpoint.h"
#include "config-edit-server.h"
#include "rc-runtime.h"
#ifndef WR_IOT_VIEW_RUNTIME_UID
#define WR_IOT_VIEW_RUNTIME_UID 0
#endif
static struct wr_iot_status_endpoint view_endpoint;
static pid_t owner;
static int listening,disabled,parent_fd=-1;
static dev_t parent_device;
static ino_t parent_inode;
static unsigned long long next_init;
static unsigned long long milliseconds(void)
{
 struct timespec now;
 if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
    (unsigned long long)now.tv_sec>(~0ULL-999)/1000)return 0;
 return (unsigned long long)now.tv_sec*1000+(unsigned long long)now.tv_nsec/1000000;
}
static int directory_current(int fd,const char *path,dev_t device,ino_t inode)
{
 struct stat held,named;
 return fd>=0&&!fstat(fd,&held)&&!lstat(path,&named)&&
  S_ISDIR(held.st_mode)&&S_ISDIR(named.st_mode)&&held.st_uid==WR_IOT_VIEW_RUNTIME_UID&&
  named.st_uid==WR_IOT_VIEW_RUNTIME_UID&&(held.st_mode&07777)==0700&&
  (named.st_mode&07777)==0700&&held.st_dev==device&&held.st_ino==inode&&
  named.st_dev==device&&named.st_ino==inode;
}
static void close_parent(void)
{
 struct stat held;
 if(parent_fd>=0&&!fstat(parent_fd,&held)&&S_ISDIR(held.st_mode)&&
    held.st_dev==parent_device&&held.st_ino==parent_inode)close(parent_fd);
 parent_fd=-1;parent_device=0;parent_inode=0;
}
int wr_iot_rc_view_runtime_close(void)
{
 int removed=0;
 if(owner!=getpid())return 0;
 if(view_endpoint.owner)removed=wr_iot_status_endpoint_close(&view_endpoint);
 close_parent();listening=0;disabled=1;return removed;
}
static void initialize(void)
{
 struct wr_iot_mailbox parent;struct stat held,child;unsigned long long now;
 int child_fd=-1,duplicate=-1;
 if(owner!=getpid()||listening||disabled)return;
 if(geteuid()!=WR_IOT_VIEW_RUNTIME_UID){disabled=1;return;}
 now=milliseconds();if(!now||now>~0ULL-1000||(next_init&&now<next_init))return;
 next_init=now+1000;wr_iot_mailbox_init(&parent);
 if(!wr_iot_mailbox_open(&parent,WR_IOT_CONTROL_DIRECTORY,1))return;
 if(fstat(parent.directory,&held)||!directory_current(parent.directory,WR_IOT_CONTROL_DIRECTORY,held.st_dev,held.st_ino))goto done;
 if(mkdirat(parent.directory,"view",0700)&&errno!=EEXIST)goto done;
 child_fd=openat(parent.directory,"view",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 if(child_fd<0||fstat(child_fd,&child)||
    !directory_current(child_fd,WR_IOT_CONFIG_VIEW_DIRECTORY,child.st_dev,child.st_ino))goto done;
 if(close(child_fd)){child_fd=-1;goto done;}child_fd=-1;
 duplicate=fcntl(parent.directory,F_DUPFD_CLOEXEC,0);if(duplicate<0)goto done;
 if(!wr_iot_status_endpoint_listen(&view_endpoint,WR_IOT_CONFIG_VIEW_DIRECTORY,WR_IOT_VIEW_RUNTIME_UID))goto done;
 if(!directory_current(duplicate,WR_IOT_CONTROL_DIRECTORY,held.st_dev,held.st_ino)){
  (void)wr_iot_status_endpoint_close(&view_endpoint);goto done;
 }
 parent_fd=duplicate;duplicate=-1;parent_device=held.st_dev;parent_inode=held.st_ino;listening=1;
 done:if(child_fd>=0)close(child_fd);if(duplicate>=0)close(duplicate);wr_iot_mailbox_close(&parent);
}
static int ready_fd(void)
{
 int fd;
 if(owner!=getpid()||!listening||disabled)return -1;
 fd=wr_iot_status_endpoint_ready_fd(&view_endpoint);
 if(fd<0||!directory_current(parent_fd,WR_IOT_CONTROL_DIRECTORY,parent_device,parent_inode)){
  (void)wr_iot_rc_view_runtime_close();return -1;
 }
 return fd;
}
static unsigned int delay_ms(void)
{
 if(owner!=getpid()||disabled)return 0;
 return !listening?1000:view_endpoint.connection>=0?100:0;
}
static void step(void)
{
 if(ready_fd()>=0)(void)wr_iot_config_view_endpoint_step(&view_endpoint,120,wr_iot_rc_edit_view);
}
int wr_iot_rc_view_runtime_install(void)
{
 const struct wr_iot_rc_view_hooks hooks={initialize,ready_fd,delay_ms,step};
 if(owner||!wr_iot_rc_edit_backend_ready()||!wr_iot_rc_runtime_register_view(&hooks))return 0;
 owner=getpid();wr_iot_status_endpoint_init(&view_endpoint);return 1;
}
