#include "action-session.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 struct wr_action_session s={0},saved;struct wr_action_event e={0};
 e.session=7;e.sequence=1;e.uptime_ms=100;e.mac[0]=2;
 e.source=WR_ACTION_STEERING;e.operation=WR_ACTION_ALLOW;e.stage=WR_ACTION_INTENT;
 assert(wr_action_session_accept(&s,12,30,100,&e)==1);
 saved=s;assert(!wr_action_session_accept(&s,12,30,100,&e));assert(!memcmp(&s,&saved,sizeof(s)));
 e.sequence=4;e.uptime_ms=101;assert(wr_action_session_accept(&s,12,30,101,&e)==2);assert(s.missing==2);
 saved=s;e.sequence=5;e.session=8;assert(!wr_action_session_accept(&s,12,30,102,&e));assert(!memcmp(&s,&saved,sizeof(s)));
 e.session=7;e.uptime_ms=99;assert(!wr_action_session_accept(&s,12,30,102,&e));
 e.uptime_ms=103;assert(!wr_action_session_accept(&s,12,30,102,&e));
 e.sequence=1;e.uptime_ms=104;e.session=8;assert(wr_action_session_accept(&s,12,31,104,&e)==1);assert(!s.missing);
 saved=s;assert(!wr_action_session_accept(&s,12,0,104,&e));assert(!memcmp(&s,&saved,sizeof(s)));
 e.sequence=3;s.missing=UINT64_MAX;assert(wr_action_session_accept(&s,12,31,104,&e)==2);assert(s.missing==UINT64_MAX);
 puts("PASS session continuity, replay/time rejection, PID reuse and explicit bounded gaps; owner verification remains caller responsibility");return 0;
}
