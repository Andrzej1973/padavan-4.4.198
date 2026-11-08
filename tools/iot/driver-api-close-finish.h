/* Synchronous reference-only finish. Retains the API owner/ticket and clears
 * the borrowed task pointer before returning to user space. Neither outcome
 * authorizes resource/lifetime pin release or network isolation removal. */
#ifndef WR_IOT_DRIVER_API_CLOSE_FINISH_H
#define WR_IOT_DRIVER_API_CLOSE_FINISH_H
#include "driver-api-close-completion.h"
static inline int wr_iot_driver_close_finish_reference(
 struct wr_iot_driver_close_owner *owner,const void *task,const void *dev,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,unsigned int vendor_count,int linux_status)
{
 int completed;
 if(!owner||!task||!dev||!owner->active||owner->task!=task||owner->device!=dev||
    owner->reference_completed||owner->uncertain)return 0;
 completed=linux_status==0&&wr_iot_driver_close_reference_completed(owner,task,dev,
   radio,slots,count,main_dev,vendor_count);
 owner->reference_completed=completed?1U:0U;owner->uncertain=completed?0U:1U;
 owner->task=0;
 /* Keep active and all nonsecret ticket/reference provenance. A separate
  * recovery owner must acquire/preserve lifetime pins, establish RF safety,
  * and explicitly retire this state. No automatic retry or reset here. */
 return completed;
}
#endif
