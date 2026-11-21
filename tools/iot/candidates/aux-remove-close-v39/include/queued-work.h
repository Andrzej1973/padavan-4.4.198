/* Isolated internal queue plumbing. Adapter lifetime must be held by caller;
 * this header does not establish MCU/reset exclusion or perform radio work. */
#ifndef WR_IOT_QUEUED_WORK_H
#define WR_IOT_QUEUED_WORK_H
#include "queued-cleanup.h"
NDIS_STATUS wr_iot_enqueue_internal_cmd(PRTMP_ADAPTER,NDIS_OID,PVOID,UINT32);
static inline NDIS_STATUS wr_iot_queue_submit(PRTMP_ADAPTER ad,
 struct wr_iot_queued_result **result)
{
 struct wr_iot_queued_result *r;
 struct wr_iot_queue_envelope e;
 NDIS_STATUS status;
 *result=NULL;
 r=wr_iot_result_alloc();
 if(!r)return NDIS_STATUS_RESOURCES;
 e.result=r;wr_iot_result_get(r); /* reserve before publishing envelope */
 status=wr_iot_enqueue_internal_cmd(ad,WR_IOT_CMD_QUEUED_RADIO,&e,sizeof(e));
 if(status!=NDIS_STATUS_SUCCESS){
  wr_iot_result_cancel(r);wr_iot_result_put(r);wr_iot_result_put(r);
  return status;
 }
 *result=r;return NDIS_STATUS_SUCCESS;
}
/* Worker never owns the caller's ref. Generic cleanup releases queue ref.
 * NULL operation deliberately fails closed until reviewed radio binding.
 */
static inline int wr_iot_queue_dispatch(PRTMP_ADAPTER ad,PCmdQElmt cmd,
 int (*execute)(PRTMP_ADAPTER))
{
 struct wr_iot_queue_envelope *e;
 int status;
 if(cmd->command!=WR_IOT_CMD_QUEUED_RADIO)return 0;
 if(cmd->CmdFromNdis||!cmd->buffer||
    cmd->bufferlength!=sizeof(*e))return 1;
 e=(struct wr_iot_queue_envelope *)cmd->buffer;
 if(!e->result||!wr_iot_result_start(e->result))return 1;
 status=execute?execute(ad):-1;
 wr_iot_result_finish(e->result,status);
 return 1;
}
#endif
