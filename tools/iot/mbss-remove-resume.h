/* Host model for resuming one MBSS removal without repeating a mutation.
 * Caller holds the adapter transition lock and owns the allocation until
 * final release. Do not hold dev_hold across rtnl_unlock: netdev_run_todo
 * waits for all kernel netdev references to drain.
 * reports_drained must be proved from the hardware TxS/RX path. A zero
 * WrBeaconTxSOutstanding software snapshot is not this proof. */
#ifndef WR_IOT_MBSS_REMOVE_RESUME_H
#define WR_IOT_MBSS_REMOVE_RESUME_H
#include "interface-registry.h"
#include "mbss-retirement.h"
enum wr_iot_mbss_remove_step {
 WR_MBSS_REMOVE_WAIT=0, WR_MBSS_REMOVE_BEACON,
 WR_MBSS_REMOVE_UNREGISTER, WR_MBSS_REMOVE_RECORD_KERNEL,
 WR_MBSS_REMOVE_VENDOR, WR_MBSS_REMOVE_RELEASE
};
static inline enum wr_iot_mbss_remove_step wr_iot_mbss_remove_next(
 const struct wr_iot_interface_ref *r,const struct wr_bss_retirement *b,
 const void *device,unsigned long generation,int callbacks_quiescent,
 int reports_drained){
 if(!r||!b||!device||!generation||r->device!=device||
    r->generation!=generation||b->generation!=generation||
    r->family!=WR_REF_FAMILY_MBSS||!r->published||!r->removing||
    r->removal_stage>1)return WR_MBSS_REMOVE_WAIT;
 if(b->stage==WR_BSS_REMOVING&&r->removal_stage==0&&
    r->phase==WR_REF_IDLE&&wr_iot_registry_checked_close_terminal(r))
  return WR_MBSS_REMOVE_BEACON;
 if(b->stage==WR_BSS_BEACON_DONE&&r->removal_stage==0&&
    r->phase==WR_REF_IDLE&&wr_iot_registry_checked_close_terminal(r))
  return WR_MBSS_REMOVE_UNREGISTER;
 if(b->stage==WR_BSS_BEACON_DONE&&r->removal_stage==1)
  return WR_MBSS_REMOVE_RECORD_KERNEL;
 if(b->stage==WR_BSS_KERNEL_DONE&&r->removal_stage==1&&
    r->phase==WR_REF_IDLE&&wr_iot_registry_checked_close_terminal(r)&&
    callbacks_quiescent&&reports_drained)
  return WR_MBSS_REMOVE_VENDOR;
 if(b->stage==WR_BSS_VENDOR_DONE&&r->removal_stage==1&&
    r->phase==WR_REF_IDLE&&wr_iot_registry_checked_close_terminal(r)&&
    callbacks_quiescent&&reports_drained)
  return WR_MBSS_REMOVE_RELEASE;
 return WR_MBSS_REMOVE_WAIT;
}
#endif
