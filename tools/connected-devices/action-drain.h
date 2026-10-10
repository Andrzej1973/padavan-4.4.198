#ifndef WR_ACTION_DRAIN_H
#define WR_ACTION_DRAIN_H
#include "action-owner.h"
#include "action-receive.h"
#include "action-session.h"
#define WR_ACTION_RING_MAX 256
#define WR_ACTION_DRAIN_MAX 16
struct wr_action_log {
 struct wr_action_session session;struct wr_action_event events[WR_ACTION_RING_MAX];
 size_t first,count;uint64_t dropped,rejected;int owner_available;
};
static inline void wr_action_count(uint64_t *n){if(*n<UINT64_MAX)(*n)++;}
/* Caller supplies an already opened credential-enabled nonblocking socket.
 * At most sixteen datagrams are consumed per tick. Ownership is rechecked
 * after receipt before evidence is committed; failures retain old RAM history. */
static inline void wr_action_drain(struct wr_action_log *log,int fd,
 const char *lock,const char *executable,const char *proc,uint64_t now){
 struct wr_action_owner before,after;struct wr_action_event e;unsigned i;int result;
 if(!log||fd<0)return;
 log->owner_available=wr_action_owner_verify(lock,executable,proc,0,&before);
 for(i=0;i<WR_ACTION_DRAIN_MAX;i++){
  /* Drain unauthenticated queued data even if the daemon is absent. */
  result=wr_action_receive(fd,log->owner_available?before.pid:1,0,&e);
  if(!result)break;
  if(result<0||!log->owner_available){wr_action_count(&log->rejected);continue;}
  if(!wr_action_owner_verify(lock,executable,proc,0,&after)||
     before.pid!=after.pid||before.birth!=after.birth){
   log->owner_available=0;wr_action_count(&log->rejected);continue;
  }
  if(!wr_action_session_accept(&log->session,before.pid,before.birth,now,&e)){
   wr_action_count(&log->rejected);continue;
  }
  if(log->count==WR_ACTION_RING_MAX){log->first=(log->first+1)%WR_ACTION_RING_MAX;log->count--;wr_action_count(&log->dropped);}
  log->events[(log->first+log->count)%WR_ACTION_RING_MAX]=e;log->count++;
 }
}
#endif
