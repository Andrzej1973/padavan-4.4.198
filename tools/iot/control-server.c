#define _GNU_SOURCE
#include "control-channel.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
int wr_iot_rc_dispatch(void){
 struct wr_iot_mailbox m;struct wr_iot_control_request request={0};
 struct wr_iot_control_result previous;
 enum wr_iot_result_state outcome;unsigned long long now;int claimed,finished=0,pending,retain_shutdown=0;
 if(!wr_iot_rc_shutdown_begin())return 0;
 now=wr_iot_control_now();if(!now)goto done;
 wr_iot_mailbox_init(&m);
 if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0))goto done;
 claimed=wr_iot_mailbox_claim(&m,now,&request);
 if(!claimed){
  /* Retry only credential-file cleanup after an already terminal result.
   * Never replay a RUNNING or RECOVERY operation after interruption. */
  finished=wr_iot_mailbox_result(&m,&previous)&&
   (previous.state==WR_IOT_RESULT_APPLIED||previous.state==WR_IOT_RESULT_REJECTED)&&
   wr_iot_mailbox_finish(&m,previous.id,previous.state,now);
  wr_iot_mailbox_close(&m);goto done;
 }
 wr_iot_mailbox_close(&m);
 /* RUNNING is visible before execution and prevents replay/replacement even
  * when RC dies or its backend cannot finish recovery. Do not hold the queue
  * lock while taking the distinct activation/service guard. */
 outcome=wr_iot_activation_execute(&request);
 if(outcome!=WR_IOT_RESULT_APPLIED&&outcome!=WR_IOT_RESULT_REJECTED)
  outcome=WR_IOT_RESULT_RECOVERY;
 /* Recovery still owns resources/isolation after this request returns.
  * Do not replay a pending shutdown into the stock fatal path, which would
  * continue LAN teardown even if the Wi-Fi stop helper refuses. Only a
  * separately confirmed recovery owner may release this admission fence. */
 retain_shutdown=outcome==WR_IOT_RESULT_RECOVERY;
 now=wr_iot_control_now();
 if(!now||!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0)){
  memset(&request,0,sizeof(request));goto done;
 }
 finished=wr_iot_mailbox_finish(&m,request.id,outcome,now);
 wr_iot_mailbox_close(&m);memset(&request,0,sizeof(request));
done:
 /* Only terminal activation results may release this request's fence.
  * RECOVERY keeps both admission and the first pending shutdown signal;
  * result publication does not establish resource or RF retirement. */
 if(retain_shutdown)return finished;
 pending=wr_iot_rc_shutdown_end();
 if(pending)raise(pending);
 return finished;
}
