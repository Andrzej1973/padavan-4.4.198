/* All reads hold the transition lock. Fresh/externally joined storage only;
 * a zero deferred counter alone is not a release or reopen receipt.
 * Actual work joins and every raw adapter free remain caller obligations. */
#ifndef WR_IOT_MBSS_RECOVERY_STORAGE_H
#define WR_IOT_MBSS_RECOVERY_STORAGE_H
#include "mbss-close-recovery-owner.h"
static inline int wr_iot_mbss_recovery_storage_idle(
 const struct wr_iot_mbss_recovery_owner *owners,unsigned int count)
{
 unsigned int i;
 if(!owners||!count)return 0;
 for(i=0;i<count;i++){
  const struct wr_iot_mbss_recovery_owner *o=&owners[i];
  if(o->phase!=WR_MBSS_OWNER_IDLE||o->device||o->generation||o->open_token||
     o->close_serial||o->close_ticket_valid||o->deferred_owners||o->attempts||
     o->stop_requested||o->completed)return 0;
 }
 return 1;
}
#endif
