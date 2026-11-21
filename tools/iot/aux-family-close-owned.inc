/* Non-last auxiliary close only. Caller/RTNL pins adapter, netdev and module.
 * The original module pin is consumed only after exact-ticket finalization.
 * Failure retains all ownership; no automatic recovery worker is installed. */
#include "aux-close-claim.h"
static INT wr_iot_aux_family_close_owned(RTMP_ADAPTER *ad,PNET_DEV dev,
 enum wr_iot_ref_family family,INT (*family_close)(RTMP_ADAPTER *,PNET_DEV))
{
 struct wr_iot_interface_ref *record;
 struct wr_iot_family_close *state;
 struct wr_iot_radio_ticket ticket;
 unsigned long generation=0;
 unsigned int slot;
 ULONG flags;int admitted=0,result,consumed=0;
 if(!ad||!dev||!family_close||
    (family!=WR_REF_FAMILY_APCLI&&family!=WR_REF_FAMILY_MONITOR))return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev);
 if(!record||record->family!=family)goto reject;
 slot=(unsigned int)(record-ad->wr_iot_interface_refs);
 state=&ad->wr_iot_family_close[slot];
 /* A new acquired open may reuse a completed logical close, never a failed
  * one. Its token/generation must differ from the completed operation. */
 if(state->phase==WR_FAMILY_CLOSE_DONE&&
    (state->generation!=record->generation||state->token!=record->last_token))
  wr_iot_family_close_init(state);
 if(state->phase!=WR_FAMILY_CLOSE_IDLE)goto reject;
 admitted=wr_iot_aux_close_reserve(&ad->wr_iot_transition,
  ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,family,VIRTUAL_IF_NUM(ad),
  &ticket,&generation);
 if(!admitted||!wr_iot_family_close_begin(state,record))goto reject;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);

 result=family_close(ad,dev); /* May mutate; never invoke under spinlock. */
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_family_close_result(state,record,result==NDIS_STATUS_SUCCESS))goto reject;
 if(result!=NDIS_STATUS_SUCCESS){record->close_stage=6;goto reject;}
 if(ad->wr_iot_transition.epoch!=ticket.epoch||
    ad->wr_iot_transition.serial!=ticket.serial||
    ad->wr_iot_transition.busy!=WR_RADIO_AUX_CLOSE){
  state->phase=WR_FAMILY_CLOSE_UNCERTAIN;record->close_stage=6;goto reject;
 }
 if(!wr_iot_family_down_begin(state,record))goto reject;
 record->close_stage=1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_DEREG(dev);
#endif
 result=wr_iot_virtual_down_checked(ad,&ticket);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(result!=NDIS_STATUS_SUCCESS){
  int unmutated=ad->wr_iot_transition.virtual_down_stage==0&&
   ad->wr_iot_transition.epoch==ticket.epoch&&
   ad->wr_iot_transition.serial==ticket.serial&&
   VIRTUAL_IF_NUM(ad)==record->close_vendor_count;
  (void)wr_iot_family_down_result(state,record,0,unmutated);
  if(!unmutated)record->close_stage=6;
  goto reject;
 }
 if(!wr_iot_family_down_result(state,record,1,0)||
    !wr_iot_family_close_finish(state,record))goto reject;
 consumed=wr_iot_aux_close_finalize_after_down(&ad->wr_iot_transition,
  ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket,1,VIRTUAL_IF_NUM(ad));
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!consumed)return -EBUSY;
 wake_up_all(&ad->wr_iot_ticket_wait);
 RT_MOD_DEC_USE_COUNT();return 0;
reject:
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return -EBUSY;
}
