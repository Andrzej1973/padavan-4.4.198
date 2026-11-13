#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "driver-close-controller.h"
static enum wr_iot_driver_close_submit_result close_result,progress_result,release_result;
static unsigned closes,progresses,releases;
int wr_iot_driver_close_request_from_open(struct wr_iot_driver_close_request *out,
 const struct wr_iot_driver_attempt *attempt,const struct wr_iot_driver_open_current_result *receipt)
{
 if(!out||!attempt||!receipt||!receipt->open_token||
    attempt->identity.adapter_epoch!=receipt->adapter_epoch||
    attempt->identity.device_generation!=receipt->device_generation)return 0;
 memset(out,0,sizeof(*out));out->open_request_id[0]=attempt->request_id[0];
 out->adapter_epoch=receipt->adapter_epoch;out->device_generation=receipt->device_generation;
 out->open_token=receipt->open_token;return 1;
}
enum wr_iot_driver_close_submit_result wr_iot_driver_close_submit(const struct wr_iot_driver_close_request *r)
{assert(r->open_request_id[0]==1&&r->open_token==3);closes++;return close_result;}
enum wr_iot_driver_close_submit_result wr_iot_driver_close_progress_submit(const struct wr_iot_driver_close_request *r)
{assert(r->open_request_id[0]==1&&r->open_token==3);progresses++;return progress_result;}
enum wr_iot_driver_close_submit_result wr_iot_driver_close_release_submit(const struct wr_iot_driver_close_request *r)
{assert(r->open_request_id[0]==1&&r->open_token==3);releases++;return release_result;}
#include "driver-close-controller.c"
int main(void)
{
 struct wr_iot_driver_attempt attempt={{1,2},{1}};
 struct wr_iot_driver_open_current_result receipt={1,2,3};
 struct wr_iot_close_controller state={0};
 close_result=WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED;
 assert(!wr_iot_close_controller_begin(&state,&attempt,&receipt)&&state.phase==WR_IOT_CLOSE_IDLE&&!state.request.open_token);
 close_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(wr_iot_close_controller_begin(&state,&attempt,&receipt)&&state.phase==WR_IOT_CLOSE_SUBMITTED);
 assert(!wr_iot_close_controller_begin(&state,&attempt,&receipt)&&closes==2);
 progress_result=WR_IOT_DRIVER_CLOSE_PENDING;
 assert(!wr_iot_close_controller_progress(&state)&&state.phase==WR_IOT_CLOSE_SUBMITTED);
 progress_result=WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED;
 assert(!wr_iot_close_controller_progress(&state)&&state.phase==WR_IOT_CLOSE_SUBMITTED);
 progress_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(wr_iot_close_controller_progress(&state)&&state.phase==WR_IOT_CLOSE_REFERENCE_RETIRED);
 assert(!wr_iot_close_controller_progress(&state)&&progresses==3);
 memset(&state,0,sizeof(state));close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 assert(!wr_iot_close_controller_begin(&state,&attempt,&receipt)&&state.phase==WR_IOT_CLOSE_UNCERTAIN);
 progress_result=WR_IOT_DRIVER_CLOSE_PENDING;
 assert(!wr_iot_close_controller_progress(&state)&&state.request.open_token==3&&state.phase==WR_IOT_CLOSE_UNCERTAIN);
 progress_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(wr_iot_close_controller_progress(&state)&&state.phase==WR_IOT_CLOSE_REFERENCE_RETIRED);
 memset(&state,0,sizeof(state));close_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(wr_iot_close_controller_begin(&state,&attempt,&receipt));progress_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 assert(!wr_iot_close_controller_progress(&state)&&state.phase==WR_IOT_CLOSE_UNCERTAIN);
 struct wr_iot_driver_close_request retained=state.request;
 unsigned close_count=closes;
 assert(!wr_iot_close_controller_begin(&state,&attempt,&receipt)&&closes==close_count);
 progress_result=WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED;
 assert(!wr_iot_close_controller_progress(&state)&&state.phase==WR_IOT_CLOSE_UNCERTAIN);
 progress_result=WR_IOT_DRIVER_CLOSE_PENDING;
 assert(!wr_iot_close_controller_progress(&state)&&state.phase==WR_IOT_CLOSE_UNCERTAIN);
 assert(!memcmp(&state.request,&retained,sizeof(retained)));
 progress_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(wr_iot_close_controller_progress(&state)&&state.phase==WR_IOT_CLOSE_REFERENCE_RETIRED);
 unsigned progress_count=progresses;
 assert(!wr_iot_close_controller_progress(&state)&&progresses==progress_count&&closes==close_count);
 assert(!wr_iot_close_controller_begin(&state,&attempt,&receipt)&&closes==close_count);
 release_result=WR_IOT_DRIVER_CLOSE_PENDING;
 assert(!wr_iot_close_controller_release(&state)&&state.phase==WR_IOT_CLOSE_RELEASE_PENDING);
 assert(!wr_iot_close_controller_progress(&state)&&progresses==progress_count);
 release_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 assert(!wr_iot_close_controller_release(&state)&&state.phase==WR_IOT_CLOSE_RELEASE_UNCERTAIN);
 release_result=WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED;
 assert(!wr_iot_close_controller_release(&state)&&state.phase==WR_IOT_CLOSE_RELEASE_UNCERTAIN);
 assert(!memcmp(&state.request,&retained,sizeof(retained)));
 release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(wr_iot_close_controller_release(&state)&&state.phase==WR_IOT_CLOSE_OWNER_RELEASED);
 unsigned release_count=releases;
 assert(wr_iot_close_controller_release(&state)&&releases==release_count);
 assert(!wr_iot_close_controller_begin(&state,&attempt,&receipt)&&closes==close_count);
 assert(!wr_iot_close_controller_release(NULL));
 /* Recovery polling must not report quiescence at mere reference retirement
  * and may issue at most one ioctl, with no hidden CLOSE retry. */
 memset(&state,0,sizeof(state));
 unsigned old_closes=closes,old_progress=progresses,old_releases=releases;
 assert(!wr_iot_close_controller_advance(NULL));
 assert(!wr_iot_close_controller_advance(&state));
 assert(closes==old_closes&&progresses==old_progress&&releases==old_releases);
 close_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(wr_iot_close_controller_begin(&state,&attempt,&receipt));
 progress_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(!wr_iot_close_controller_advance(&state));
 assert(state.phase==WR_IOT_CLOSE_REFERENCE_RETIRED);
 assert(progresses==old_progress+1&&releases==old_releases&&closes==old_closes+1);
 release_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;
 assert(!wr_iot_close_controller_advance(&state));
 assert(state.phase==WR_IOT_CLOSE_RELEASE_UNCERTAIN&&releases==old_releases+1);
 release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
 assert(wr_iot_close_controller_advance(&state));
 assert(releases==old_releases+2&&closes==old_closes+1&&progresses==old_progress+1);
 assert(wr_iot_close_controller_advance(&state)&&releases==old_releases+2);
 puts("PASS single CLOSE submission, retained uncertain ownership and one-ioctl recovery steps; retirement is not owner release");return 0;
}
