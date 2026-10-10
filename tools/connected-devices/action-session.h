#ifndef WR_ACTION_SESSION_H
#define WR_ACTION_SESSION_H
#include "action-event.h"
#include <sys/types.h>
#include <string.h>
struct wr_action_session {
 pid_t pid; uint64_t birth,session,sequence,uptime_ms,missing;
};
/* The caller must verify live executable/lock ownership and process birth
 * before every drain. This gate does not establish process identity itself.
 * Return 0 for rejection, 1 for continuity, 2 for an accepted gap. */
static inline int wr_action_session_accept(struct wr_action_session *s,
 pid_t verified_pid,uint64_t verified_birth,uint64_t now,
 const struct wr_action_event *e){
 uint64_t lost;int gap;
 if(!s||verified_pid<=0||!verified_birth||!wr_action_valid(e)||
    e->source!=WR_ACTION_STEERING||e->uptime_ms>now)return 0;
 if(s->pid!=verified_pid||s->birth!=verified_birth){
  memset(s,0,sizeof(*s));s->pid=verified_pid;s->birth=verified_birth;
 }
 if(s->session&&s->session!=e->session)return 0;
 if(e->sequence<=s->sequence||(s->session&&e->uptime_ms<s->uptime_ms))return 0;
 lost=e->sequence-s->sequence-1;gap=lost!=0;
 s->missing=UINT64_MAX-s->missing<lost?UINT64_MAX:s->missing+lost;
 s->session=e->session;s->sequence=e->sequence;s->uptime_ms=e->uptime_ms;
 return gap?2:1;
}
#endif
