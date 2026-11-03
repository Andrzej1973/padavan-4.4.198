#include "mbss-poll-lifetime.h"
#include <assert.h>
int main(void){
 struct wr_iot_mbss_poll_lifetime s;
 wr_iot_mbss_poll_init(&s);
 assert(!wr_iot_mbss_poll_release_ready(&s));
 assert(wr_iot_mbss_poll_reserve(&s));
 assert(wr_iot_mbss_poll_queue_result(&s,1));
 assert(!wr_iot_mbss_poll_reserve(&s));
 assert(wr_iot_mbss_poll_begin(&s));
 assert(!wr_iot_mbss_poll_joined(&s,1));
 wr_iot_mbss_poll_returned(&s);
 assert(!wr_iot_mbss_poll_reserve(&s));
 assert(!wr_iot_mbss_poll_joined(&s,0));
 assert(wr_iot_mbss_poll_joined(&s,1));
 assert(wr_iot_mbss_poll_reserve(&s));
 wr_iot_mbss_poll_stop(&s);
 assert(!wr_iot_mbss_poll_begin(&s)); /* callback must skip poll body */
 assert(s.running&&!wr_iot_mbss_poll_release_ready(&s));
 wr_iot_mbss_poll_returned(&s);
 assert(!wr_iot_mbss_poll_release_ready(&s));
 assert(wr_iot_mbss_poll_joined(&s,1));
 assert(wr_iot_mbss_poll_release_ready(&s));
 assert(!wr_iot_mbss_poll_reserve(&s));
 wr_iot_mbss_poll_init(&s);
 for(unsigned int i=0;i<3;i++){
  assert(wr_iot_mbss_poll_reserve(&s));
  assert(wr_iot_mbss_poll_queue_result(&s,0));
  assert(s.unjoined&&!wr_iot_mbss_poll_reserve(&s));
  assert(wr_iot_mbss_poll_joined(&s,1));
 }
 assert(!wr_iot_mbss_poll_reserve(&s));
 wr_iot_mbss_poll_stop(&s);
 assert(wr_iot_mbss_poll_release_ready(&s));
 wr_iot_mbss_poll_init(&s);
 assert(wr_iot_mbss_poll_reserve(&s));
 assert(wr_iot_mbss_poll_queue_result(&s,1));
 for(unsigned int i=0;i<3;i++){
  assert(wr_iot_mbss_poll_begin(&s));
  if(i<2){
   assert(wr_iot_mbss_poll_rearm(&s));
   assert(wr_iot_mbss_poll_queue_result(&s,1));
  }else assert(!wr_iot_mbss_poll_rearm(&s));
  wr_iot_mbss_poll_returned(&s);
  assert(s.unjoined);
 }
 wr_iot_mbss_poll_stop(&s);
 assert(!wr_iot_mbss_poll_release_ready(&s));
 assert(wr_iot_mbss_poll_joined(&s,1));
 assert(wr_iot_mbss_poll_release_ready(&s));
 wr_iot_mbss_poll_init(&s);
 assert(wr_iot_mbss_poll_reserve(&s));
 assert(wr_iot_mbss_poll_queue_result(&s,1));
 assert(wr_iot_mbss_poll_begin(&s));
 assert(wr_iot_mbss_poll_rearm(&s));
 assert(wr_iot_mbss_poll_queue_result(&s,0));
 assert(s.unjoined&&s.running&&!s.pending);
 wr_iot_mbss_poll_stop(&s);
 assert(!wr_iot_mbss_poll_rearm(&s));
 wr_iot_mbss_poll_returned(&s);
 assert(!wr_iot_mbss_poll_release_ready(&s));
 assert(wr_iot_mbss_poll_joined(&s,1));
 assert(wr_iot_mbss_poll_release_ready(&s));
 wr_iot_mbss_poll_init(&s);
 assert(wr_iot_mbss_poll_reserve(&s));
 assert(wr_iot_mbss_poll_queue_result(&s,1));
 assert(wr_iot_mbss_poll_join_enter(&s));
 assert(!wr_iot_mbss_poll_join_enter(&s));
 assert(!wr_iot_mbss_poll_reserve(&s));
 assert(wr_iot_mbss_poll_joined(&s,1));
 assert(wr_iot_mbss_poll_join_leave(&s,1)&&s.attempts==0);
 assert(wr_iot_mbss_poll_reserve(&s)); /* next recovery episode */
 assert(wr_iot_mbss_poll_begin(&s));
 assert(wr_iot_mbss_poll_join_enter(&s));
 assert(!wr_iot_mbss_poll_rearm(&s));
 wr_iot_mbss_poll_stop(&s);
 wr_iot_mbss_poll_returned(&s);
 assert(wr_iot_mbss_poll_joined(&s,1));
 assert(!wr_iot_mbss_poll_release_ready(&s));
 assert(wr_iot_mbss_poll_join_leave(&s,1));
 assert(wr_iot_mbss_poll_release_ready(&s));
 assert(!wr_iot_mbss_poll_reserve(&s));
 return 0;
}
