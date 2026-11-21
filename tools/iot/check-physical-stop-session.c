#include <assert.h>
#include <string.h>
#include "physical-stop-session.h"
#include "physical-stop-down.h"
static int calls,downs,reenter;
static enum wr_iot_physical_call_result outcome;
static enum wr_iot_physical_down_result down_result;
static unsigned status;
static struct wr_iot_physical_session *live;
static struct wr_iot_physical_stop_request previous;
enum wr_iot_physical_call_result wr_iot_physical_stop_call(
 const struct wr_iot_physical_stop_request *r,struct wr_iot_physical_stop_response *out)
{
 ++calls;
 if(reenter)assert(!wr_iot_physical_session_advance(live));
 previous=*r;
 if(outcome!=WR_PHYSICAL_CALL_ACKNOWLEDGED)return outcome;
 out->identity=*r;out->identity.attempt=73;
 out->status=r->action==WR_STOP_ARM?WR_STOP_ARMED:status;
 return outcome;
}
enum wr_iot_physical_down_result wr_iot_physical_stop_down(void)
{++downs;return down_result;}
int main(void)
{
 struct wr_iot_physical_stop_request r={.action=WR_STOP_ARM,.epoch=1,
  .generation=2,.open_token=3,.closed_serial=4,.nonce={5}};
 for(int mode=0;mode<3;mode++){
  struct wr_iot_physical_session s={0};int before=calls,dbefore=downs;
  live=&s;reenter=1;
  assert(wr_iot_physical_session_begin(&s,&r));assert(!wr_iot_physical_session_begin(&s,&r));
  s.owner++;assert(!wr_iot_physical_session_advance(&s)&&calls==before);s.owner--;
  outcome=WR_PHYSICAL_CALL_UNCERTAIN;
  assert(!wr_iot_physical_session_advance(&s)&&downs==dbefore);
  assert(s.phase==WR_PHYSICAL_SESSION_ARM&&!s.request.attempt);
  outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;
  assert(!wr_iot_physical_session_advance(&s)&&s.request.attempt==73);
  down_result=mode==0?WR_PHYSICAL_DOWN_NOT_SUBMITTED:mode==1?WR_PHYSICAL_DOWN_UNCERTAIN:WR_PHYSICAL_DOWN_IOCTL_RETURNED;
  assert(!wr_iot_physical_session_advance(&s)&&downs==dbefore+1);
  if(mode==0){
   outcome=WR_PHYSICAL_CALL_UNCERTAIN;assert(!wr_iot_physical_session_advance(&s));
   assert(previous.action==WR_STOP_CANCEL&&s.phase==WR_PHYSICAL_SESSION_CANCEL);
   outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;status=WR_STOP_CANCELLED;
   assert(wr_iot_physical_session_advance(&s)==-1);
  }else{
   for(status=WR_STOP_ARMED;status<=WR_STOP_FAILED;status++){
    if(status==WR_STOP_COMPLETE)continue;
    assert(!wr_iot_physical_session_advance(&s)&&s.phase==WR_PHYSICAL_SESSION_QUERY);
    assert(previous.action==WR_STOP_QUERY&&previous.attempt==73);
   }
   outcome=WR_PHYSICAL_CALL_UNCERTAIN;assert(!wr_iot_physical_session_advance(&s));
   outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;status=WR_STOP_COMPLETE;
   assert(!wr_iot_physical_session_advance(&s)&&s.phase==WR_PHYSICAL_SESSION_RELEASE);
   outcome=WR_PHYSICAL_CALL_UNCERTAIN;assert(!wr_iot_physical_session_advance(&s));
   assert(previous.action==WR_STOP_RELEASE);
   outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;status=WR_STOP_RELEASED;
   assert(wr_iot_physical_session_advance(&s)==1);
  }
  before=calls;assert(wr_iot_physical_session_advance(&s)==(mode==0?-1:1));
  assert(calls==before&&downs==dbefore+1);
 }
 return 0;
}
