/* Internal only. Outer caller owns RTNL and adapter/netdevice/module lifetime.
 * No new ioctl route or OPEN permission. Persistent adapter probe survives
 * failed ticket retirement; poison and existing free fences retain it. */
#include "physical-rebind-probe.h"
static INT __attribute__((unused)) wr_iot_physical_rebind_observe(
 RTMP_ADAPTER *ad,PNET_DEV dev,const struct wr_iot_physical_stop_request *request)
{
 ULONG flags=0;int begun=0,observed,accepted,status,wake=0,eligible;
 struct wr_iot_physical_rebind_probe *probe;
 if(!ad||!dev||!wr_iot_physical_stop_request_valid(request))return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 probe=&ad->wr_iot_physical_rebind_probe;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 eligible=IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&dev!=ad->net_dev&&
  ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&!ad->wr_iot_control_users&&
  !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
  !ad->wr_iot_close_owner.active&&!ad->wr_iot_physical_lifetime.active;
 if(eligible)begun=wr_iot_physical_rebind_probe_begin(probe,
  &ad->wr_iot_physical_terminal,task_pid(current),request,&ad->wr_iot_main_recovery,
  &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  ad->net_dev,dev,VIRTUAL_IF_NUM(ad));
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!begun)return -EBUSY;
 observed=wr_iot_mt7603_closed_config_observed(ad,dev);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 eligible=IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&dev!=ad->net_dev&&
  ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&!ad->wr_iot_control_users&&
  !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
  !ad->wr_iot_close_owner.active&&!ad->wr_iot_physical_lifetime.active;
 accepted=wr_iot_physical_rebind_probe_finish(probe,&ad->wr_iot_physical_terminal,
  task_pid(current),request,&ad->wr_iot_main_recovery,&ad->wr_iot_transition,
  ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev,dev,VIRTUAL_IF_NUM(ad),
  eligible?observed:0);
 if(probe->active){ad->wr_iot_control_poisoned=1;status=-EUCLEAN;}
 else{wake=1;status=accepted?0:-EAGAIN;}
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(wake)wake_up_all(&ad->wr_iot_ticket_wait);
 return status;
}

#include "physical-rebind-open.h"
/* Internal alternative to normal request_enter. Outer ioctl must independently
 * validate capability/copies and supply both exact requests before calling.
 * Existing ndo_open/loaded-key/first-beacon/leave paths remain mandatory. */
static INT __attribute__((unused)) wr_iot_physical_rebind_request_enter(
 RTMP_ADAPTER *ad,PNET_DEV dev,const struct wr_iot_physical_stop_request *physical,
 const struct wr_iot_driver_open_request *request)
{
 ULONG flags=0;int accepted=0;
 if(!ad||!dev||!physical||!request)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&dev!=ad->net_dev&&
    ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&!ad->wr_iot_control_users&&
    !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
    !ad->wr_iot_close_owner.active&&!ad->wr_iot_physical_lifetime.active){
  accepted=wr_iot_physical_rebind_open_reserve(&ad->wr_iot_physical_rebind_probe,
   &ad->wr_iot_physical_terminal,task_pid(current),physical,&ad->wr_iot_main_recovery,
   &ad->wr_iot_driver_owner,&ad->wr_iot_transition,ad->wr_iot_interface_refs,
   WDEV_NUM_MAX+1,ad->net_dev,dev,VIRTUAL_IF_NUM(ad),current,request,
   ad->wr_iot_control_users,ad->wr_iot_control_poisoned);
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return accepted?0:-EBUSY;
}
