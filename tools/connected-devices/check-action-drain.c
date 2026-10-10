#define _GNU_SOURCE
#include "action-drain.h"
#include "action-send.h"
#include <assert.h>
int main(void){
 int pair[2],one=1,i;struct wr_action_log log={0};struct wr_action_event e={0};
 assert(!socketpair(AF_UNIX,SOCK_DGRAM|SOCK_NONBLOCK,0,pair));
 assert(!setsockopt(pair[1],SOL_SOCKET,SO_PASSCRED,&one,sizeof(one)));
 e.session=1;e.sequence=1;e.mac[0]=2;e.source=WR_ACTION_STEERING;e.operation=WR_ACTION_ALLOW;e.stage=WR_ACTION_INTENT;
 for(i=0;i<20;i++)assert(wr_action_send(pair[0],&e));
 wr_action_drain(&log,pair[1],"/nonexistent-wr-lock","/nonexistent-wr-daemon","/proc",0);
 assert(!log.owner_available&&!log.count&&log.rejected==16);
 wr_action_drain(&log,pair[1],"/nonexistent-wr-lock","/nonexistent-wr-daemon","/proc",0);
 assert(log.rejected==20&&!log.count);close(pair[0]);close(pair[1]);
 puts("PASS bounded sixteen-message drain and absent-owner rejection without manufactured action history");return 0;
}
