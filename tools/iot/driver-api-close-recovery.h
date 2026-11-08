/* Locked metadata handoff into the EXISTING MBSS recovery owner. Caller must
 * actually own netdev/module references and an adapter-release fence before
 * supplying true flags; this helper acquires none and must not be installed
 * as a substitute for those kernel resource operations. No isolation release. */
#ifndef WR_IOT_DRIVER_API_CLOSE_RECOVERY_H
#define WR_IOT_DRIVER_API_CLOSE_RECOVERY_H
#include "driver-api-close-owner.h"
#include "mbss-close-recovery-owner.h"
static inline int wr_iot_driver_close_queue_recovery(
 const struct wr_iot_driver_close_owner *close,
 struct wr_iot_mbss_recovery_owner *recovery,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 int netdev_held,int module_held,int adapter_release_fenced)
{
 enum wr_iot_mbss_recovery_source source;
 if(!close||!recovery||!record||!radio||!netdev_held||!module_held||
    !adapter_release_fenced||!close->active||!close->consumed||
    close->task||!close->uncertain||close->reference_completed||
    close->ticket.operation!=WR_RADIO_BSS_CLOSE||
    record->device!=close->device||record->generation!=close->generation||
    record->last_token!=close->open_token||record->removing||
    record->removal_stage||record->close_running)return 0;
 if(record->phase!=WR_REF_CLOSING)return 0;
 if(record->close_stage==5U)source=WR_MBSS_RECOVERY_UNCERTAIN;
 else if(record->close_stage==2U||record->close_stage==3U)source=WR_MBSS_RECOVERY_CLOSE_INCOMPLETE;
 else return 0; /* Absent callback/early admission and completed close need a
                 * distinct pinned recovery path; never invent stage receipts. */
 return wr_iot_mbss_recovery_queue(recovery,record,radio,source,&close->ticket,
                                  netdev_held,adapter_release_fenced);
}
/* Locked ownership transfer of the EXTRA netdev hold obtained by API enter.
 * Recovery's existing external join now owns exactly one dev_put. The API's
 * extra module hold and active adapter fence remain its own responsibility.
 * Caller must schedule existing work after acceptance; schedule failure must
 * retain the queued owner, never roll back ownership or release either hold.
 * No resource operation, original-open module transfer or RF claim here. */
static inline int wr_iot_driver_close_transfer_recovery(
 struct wr_iot_driver_close_owner *close,
 struct wr_iot_mbss_recovery_owner *recovery,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio)
{
 if(!close||!close->netdev_held||!close->module_held||
    close->recovery_netdev_transferred)return 0;
 if(!close->consumed){
  /* Finish cleared the borrowed task. Existing worker will execute this
   * reserved ticket directly; do not impersonate or rerun ndo_stop. */
  if(!record||!radio||!close->active||close->task||!close->uncertain||
     close->reference_completed||record->device!=close->device||
     record->generation!=close->generation||record->last_token!=close->open_token||
     !wr_iot_mbss_recovery_queue(recovery,record,radio,
       WR_MBSS_RECOVERY_RESERVED_CLOSE,&close->ticket,1,1))return 0;
  close->consumed=1;
 }else if(!wr_iot_driver_close_queue_recovery(close,recovery,record,radio,
    close->netdev_held,close->module_held,close->active))return 0;
 close->netdev_held=0;
 close->recovery_netdev_transferred=1;
 return 1;
}
#endif
