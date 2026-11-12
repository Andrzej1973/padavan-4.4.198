#include <string.h>
#include "driver-close-controller.h"
int wr_iot_close_controller_begin(struct wr_iot_close_controller *state,
 const struct wr_iot_driver_attempt *attempt,const struct wr_iot_driver_open_current_result *receipt)
{
 enum wr_iot_driver_close_submit_result result;
 if(!state||state->phase!=WR_IOT_CLOSE_IDLE)return 0;
 if(!wr_iot_driver_close_request_from_open(&state->request,attempt,receipt))return 0;
 result=wr_iot_driver_close_submit(&state->request);
 if(result==WR_IOT_DRIVER_CLOSE_NOT_SUBMITTED){
  memset(&state->request,0,sizeof(state->request));return 0;
 }
 state->phase=result==WR_IOT_DRIVER_CLOSE_CALL_COMPLETED?
  WR_IOT_CLOSE_SUBMITTED:WR_IOT_CLOSE_UNCERTAIN;
 return state->phase==WR_IOT_CLOSE_SUBMITTED;
}
int wr_iot_close_controller_progress(struct wr_iot_close_controller *state)
{
 enum wr_iot_driver_close_submit_result result;
 if(!state||state->phase!=WR_IOT_CLOSE_SUBMITTED)return 0;
 result=wr_iot_driver_close_progress_submit(&state->request);
 if(result==WR_IOT_DRIVER_CLOSE_CALL_COMPLETED){
  state->phase=WR_IOT_CLOSE_REFERENCE_RETIRED;return 1;
 }
 if(result==WR_IOT_DRIVER_CLOSE_UNCERTAIN)state->phase=WR_IOT_CLOSE_UNCERTAIN;
 return 0;
}
