#include "peer-close-executor.h"
#include <assert.h>
int main(void){struct wr_iot_peer_close_executor s;
 wr_iot_peer_close_executor_init(&s);assert(wr_iot_peer_close_executor_idle(&s));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,0));
 assert(wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,7));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_LEGACY,0));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,7));
 assert(!wr_iot_peer_close_executor_leave(&s,WR_PEER_CLOSE_CHECKED,8,1,1));
 assert(s.running);
 assert(wr_iot_peer_close_executor_leave(&s,WR_PEER_CLOSE_CHECKED,7,0,1));
 assert(!wr_iot_peer_close_executor_idle(&s));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,8));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_LEGACY,0));
 assert(wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,7));
 assert(wr_iot_peer_close_executor_leave(&s,WR_PEER_CLOSE_CHECKED,7,0,0));
 assert(s.retained); /* A rejected retry cannot erase earlier partial work. */
 assert(wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,7));
 assert(wr_iot_peer_close_executor_leave(&s,WR_PEER_CLOSE_CHECKED,7,1,1));
 assert(wr_iot_peer_close_executor_idle(&s));
 assert(wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,9));
 assert(wr_iot_peer_close_executor_leave(&s,WR_PEER_CLOSE_CHECKED,9,0,0));
 assert(wr_iot_peer_close_executor_idle(&s)); /* Invalid first ticket, no effects. */
 assert(wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_RESET,0));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,10));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_LEGACY,0));
 assert(wr_iot_peer_close_executor_leave(&s,WR_PEER_CLOSE_RESET,0,1,1));
 assert(wr_iot_peer_close_executor_idle(&s));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_RESET,1));
 assert(wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_LEGACY,0));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,10));
 assert(wr_iot_peer_close_executor_leave(&s,WR_PEER_CLOSE_LEGACY,0,0,1));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_LEGACY,0));
 assert(!wr_iot_peer_close_executor_enter(&s,WR_PEER_CLOSE_CHECKED,10));
 return 0;
}
