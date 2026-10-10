#ifndef WR_ACTION_RUNTIME_H
#define WR_ACTION_RUNTIME_H
#include "action-endpoint.h"
#include "action-drain.h"
#ifndef WR_ACTION_DIRECTORY
#define WR_ACTION_DIRECTORY "/var/run/wr-device-observer"
#endif
#ifndef WR_ACTION_SOCKET
#define WR_ACTION_SOCKET WR_ACTION_DIRECTORY "/actions"
#endif
#ifndef WR_ACTION_OWNER_LOCK
#define WR_ACTION_OWNER_LOCK "/var/run/wr-band-steering.lock"
#endif
#ifndef WR_ACTION_EXECUTABLE
#define WR_ACTION_EXECUTABLE "/usr/sbin/wr-band-steering"
#endif
struct wr_action_runtime {struct wr_action_endpoint endpoint;struct wr_action_log log;uint64_t next_tick,last_tick;int initialized;};
static inline void wr_action_runtime_tick_owned(struct wr_action_runtime *r,uint64_t now,uid_t uid){
 struct stat st;int saved=errno;
 if(!r)return;
 if(!r->initialized){r->endpoint.fd=r->endpoint.lock_fd=-1;r->initialized=1;}
 if(now<r->last_tick)r->next_tick=0;
 if(now<r->next_tick)return;
 r->last_tick=now;
 r->log.owner_available=0;
 r->next_tick=now>UINT64_MAX-5000?UINT64_MAX:now+5000;
 if(r->endpoint.fd>=0&&(lstat(WR_ACTION_SOCKET,&st)||!S_ISSOCK(st.st_mode)||st.st_uid!=uid||(st.st_mode&0777)!=0600||st.st_dev!=r->endpoint.device||st.st_ino!=r->endpoint.inode))wr_action_endpoint_close(&r->endpoint);
 if(mkdir(WR_ACTION_DIRECTORY,0700)&&errno!=EEXIST)goto done;
 if(lstat(WR_ACTION_DIRECTORY,&st)||!S_ISDIR(st.st_mode)||st.st_uid!=uid||(st.st_mode&0777)!=0700)goto done;
 if(r->endpoint.fd<0){
  if(wr_action_endpoint_open(&r->endpoint,WR_ACTION_SOCKET))goto done;
 }
 wr_action_drain_owned(&r->log,r->endpoint.fd,WR_ACTION_OWNER_LOCK,WR_ACTION_EXECUTABLE,"/proc",uid,now);
 done:errno=saved;
}
static inline void wr_action_runtime_tick(struct wr_action_runtime *r,uint64_t now){wr_action_runtime_tick_owned(r,now,0);}
static inline void wr_action_runtime_close(struct wr_action_runtime *r){if(r&&r->initialized){wr_action_endpoint_close(&r->endpoint);r->log.owner_available=0;r->next_tick=0;}}
#endif
