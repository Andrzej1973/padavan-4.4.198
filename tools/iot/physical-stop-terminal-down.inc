/* Read-only post-RELEASE QUERY. Caller pins adapter/Main and owns RTNL.
 * No new hold/put, driver work, queue operation or firmware command. */
#include "physical-stop-origin.h"
static INT __attribute__((unused)) wr_iot_physical_stop_terminal_down(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,const struct wr_iot_physical_stop_request *query,
 unsigned char *wire,unsigned int length)
{
 struct wr_iot_physical_stop_request released;
 struct wr_iot_interface_ref *main_record,*iot_record;ULONG flags=0;int exact;
 if(!wire||length!=64)return -EINVAL;
 NdisZeroMemory(wire,length);
 if(!ad||!main_dev||!wr_iot_physical_stop_request_valid(query)||query->action!=WR_STOP_QUERY)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!IS_MT7603(ad)||ad->net_dev!=main_dev||ad->ApCfg.BssidNum!=3)return -EOPNOTSUPP;
 released=*query;released.action=WR_STOP_RELEASE;
 /* Original retained PID/nonce/tuple and fully committed cleanup receipt. */
 if(!wr_iot_physical_stop_terminal_reply(&ad->wr_iot_physical_terminal,&released,wire,length))return -EAGAIN;
 NdisZeroMemory(wire,length);
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 exact=ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&
  !ad->wr_iot_physical_pins.module&&!ad->wr_iot_physical_pins.task&&!ad->wr_iot_physical_pins.device&&
  !ad->wr_iot_physical_pending_pins.module&&!ad->wr_iot_physical_pending_pins.task&&!ad->wr_iot_physical_pending_pins.device&&
  wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor)&&
  ad->wr_iot_peer_table_owner.closed&&!ad->wr_iot_peer_table_owner.active&&
  !ad->wr_iot_peer_table_owner.retained&&!ad->wr_iot_peer_table_owner.poisoned&&
  !ad->wr_iot_peer_table_owner.transactions;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!exact)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 main_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev,
  ad->wr_iot_physical_terminal.origin.main_generation);
 iot_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  ad->ApCfg.MBSSID[2].wdev.if_dev,query->generation);
 exact=!ad->wr_iot_physical_lifetime.active&&
  wr_iot_physical_stop_origin_main_down(&ad->wr_iot_physical_terminal.origin,
   &ad->wr_iot_main_recovery,&ad->wr_iot_transition,main_record,VIRTUAL_IF_NUM(ad))&&
  wr_iot_physical_stop_origin_iot_history(&released,iot_record,ad->ApCfg.MBSSID[2].wdev.if_dev);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EAGAIN;
 return wr_iot_physical_stop_response_encode(wire,length,query,query->attempt,WR_STOP_COMPLETE)?0:-EIO;
}
