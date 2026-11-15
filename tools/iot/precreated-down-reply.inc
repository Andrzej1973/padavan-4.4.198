/* Unrouted internal response builder. Outer caller owns RTNL and pinned
 * adapter/netdev lifetime; privilege and user-copy belong to the common entry.
 * No references, sequence allocations, firmware commands or state writes. */
#include "precreated-down-wire.h"
static INT __attribute__((unused)) wr_iot_precreated_down_reply(
 PRTMP_ADAPTER ad,PNET_DEV dev,const unsigned char *query,unsigned int length,
 unsigned char *reply)
{
 unsigned char nonce[16];unsigned int i;ULONG flags=0;
 struct wr_iot_down_result result={0};struct wr_iot_interface_ref *record;
 int status;
 if(!reply||length!=64)return -EINVAL;
 /* Decode before clearing: query/reply alias is allowed. */
 status=wr_iot_down_query_decode(nonce,query,length);
 for(i=0;i<64;i++)reply[i]=0;
 if(!status||!ad||!dev)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!READ_ONCE(ad->wr_iot_recovery_storage_live))return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find_openable(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev);
 if(record){result.epoch=ad->wr_iot_transition.epoch;result.generation=record->generation;
  result.main_close_serial=ad->wr_iot_main_recovery.last_release.ticket.serial;}
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!result.epoch||!result.generation||!result.main_close_serial)return -EAGAIN;
 status=wr_iot_precreated_down_observed(ad,dev,(unsigned long)result.generation);
 if(status)return status;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 status=ad->wr_iot_transition.epoch==result.epoch&&
  ad->wr_iot_main_recovery.last_release.ticket.serial==result.main_close_serial&&
  wr_iot_precreated_down_reference(&ad->wr_iot_main_recovery,&ad->wr_iot_transition,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev,dev,
   (unsigned long)result.generation,VIRTUAL_IF_NUM(ad));
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!status)return -EAGAIN;
 return wr_iot_down_reply_encode(reply,length,nonce,result.epoch,result.generation,
  result.main_close_serial)?0:-EIO;
}
