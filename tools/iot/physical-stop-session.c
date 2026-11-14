#include <unistd.h>
#include "physical-stop-session.h"
#include "physical-stop-down.h"
int wr_iot_physical_session_begin(struct wr_iot_physical_session *s,
 const struct wr_iot_physical_stop_request *request)
{
 if(!s||s->owner||s->busy||s->phase!=WR_PHYSICAL_SESSION_IDLE||
    !wr_iot_physical_stop_request_valid(request)||request->action!=WR_STOP_ARM)return 0;
 s->request=*request;s->owner=getpid();s->phase=WR_PHYSICAL_SESSION_ARM;return 1;
}
int wr_iot_physical_session_advance(struct wr_iot_physical_session *s)
{
 struct wr_iot_physical_stop_request request;
 struct wr_iot_physical_stop_response response={0};
 enum wr_iot_physical_call_result called;
 enum wr_iot_physical_down_result down;
 int result=0;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->phase==WR_PHYSICAL_SESSION_COMPLETE)return 1;
 if(s->phase==WR_PHYSICAL_SESSION_CANCELLED)return -1;
 if(s->phase<WR_PHYSICAL_SESSION_ARM||s->phase>WR_PHYSICAL_SESSION_RELEASE)return 0;
 s->busy=1;
 if(s->phase==WR_PHYSICAL_SESSION_DOWN){
  /* Even a zero ioctl return is not ndo_stop completion. Never issue DOWN
   * again after possible submission; only the owned driver QUERY may progress. */
  down=wr_iot_physical_stop_down();
  s->phase=down==WR_PHYSICAL_DOWN_NOT_SUBMITTED?WR_PHYSICAL_SESSION_CANCEL:WR_PHYSICAL_SESSION_QUERY;
  goto done;
 }
 request=s->request;
 if(s->phase==WR_PHYSICAL_SESSION_ARM)request.action=WR_STOP_ARM;
 else if(s->phase==WR_PHYSICAL_SESSION_QUERY)request.action=WR_STOP_QUERY;
 else if(s->phase==WR_PHYSICAL_SESSION_CANCEL)request.action=WR_STOP_CANCEL;
 else request.action=WR_STOP_RELEASE;
 called=wr_iot_physical_stop_call(&request,&response);
 /* Failed/lost replies retain the identical action and issuer. Repeating ARM
  * before DOWN recovers its receipt; repeating terminal actions uses the
  * driver's exact terminal cache. QUERY does not submit recovery work. */
 if(called!=WR_PHYSICAL_CALL_ACKNOWLEDGED)goto done;
 if(s->phase==WR_PHYSICAL_SESSION_ARM){
  s->request.attempt=response.identity.attempt;
  s->request.action=WR_STOP_QUERY;s->phase=WR_PHYSICAL_SESSION_DOWN;
 }else if(s->phase==WR_PHYSICAL_SESSION_QUERY){
  if(response.status==WR_STOP_COMPLETE)s->phase=WR_PHYSICAL_SESSION_RELEASE;
  /* ARMED/RUNNING/FAILED cannot authorize release, reopen or another DOWN. */
 }else if(s->phase==WR_PHYSICAL_SESSION_CANCEL){
  s->phase=WR_PHYSICAL_SESSION_CANCELLED;result=-1;
 }else if(s->phase==WR_PHYSICAL_SESSION_RELEASE){
  s->phase=WR_PHYSICAL_SESSION_COMPLETE;result=1;
 }
 done:s->busy=0;return result;
}
