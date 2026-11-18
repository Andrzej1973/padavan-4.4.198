/* Requires a live MLME callback/adapter; uses the existing transition lock.
 * Not installed until key-writer and insertion peers share this arbiter. */
#ifndef WR_IOT_RA2_MUTATION_ADMISSION_KERNEL_H
#define WR_IOT_RA2_MUTATION_ADMISSION_KERNEL_H
#include "ra2-association-owner.h"
#include "ra2-rekey-admission.h"
/* -1 refusal; 0 native non-ra2 path; 1 caller owns a linear scope ticket. */
static inline int wr_ra2_mutation_enter(RTMP_ADAPTER *ad,
 MLME_QUEUE_ELEM *event,struct wr_ra2_assoc_ticket *ticket)
{
 ULONG flags=0;
 int admitted=0;
 if(!ad||!event||!ticket||ticket->active)return -1;
 if(!IS_MT7603(ad))return 0;
 if(event->MsgLen<LENGTH_802_11)return -1;
 if(!MAC_ADDR_EQUAL(((PHEADER_802_11)event->Msg)->Addr1,
    ad->ApCfg.MBSSID[2].wdev.bssid))return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->ApCfg.BssidNum==3&&!ad->wr_iot_ra2_key_active&&
    !ad->wr_ra2_assoc_owner.key_active&&!ad->wr_ra2_assoc_owner.poisoned){
  admitted=wr_iot_ra2_rekey_admit(&ad->wr_iot_driver_owner,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->net_dev,ad->ApCfg.MBSSID[2].wdev.if_dev,VIRTUAL_IF_NUM(ad),
   &ad->wr_iot_control_users,&ad->wr_iot_control_poisoned,
   ad->wr_iot_boot_active||ad->wr_iot_boot_failed||
   ad->wr_iot_close_owner.active||ad->wr_iot_closed_probe.active);
  if(admitted&&!wr_ra2_assoc_enter(&ad->wr_ra2_assoc_owner,ticket,0)){
   /* Only this just-admitted reference is rolled back. No unrelated actor's
    * ownership is released. This block still owns transition_lock. */
   --ad->wr_iot_control_users;admitted=0;
   if(ad->wr_ra2_assoc_owner.poisoned)ad->wr_iot_control_poisoned=1;
  }
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return admitted?1:-1;
}
static inline void wr_ra2_mutation_leave(RTMP_ADAPTER *ad,
 struct wr_ra2_assoc_ticket *ticket)
{
 ULONG flags=0;
 if(!ad||!ticket)return;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 /* A foreign/inactive ticket owns no reference on this adapter. */
 if(!ticket->active||ticket->owner!=&ad->wr_ra2_assoc_owner){
  ad->wr_iot_control_poisoned=1;
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return;
 }
 if(!wr_ra2_assoc_leave(&ad->wr_ra2_assoc_owner,ticket))
  ad->wr_iot_control_poisoned=1;
 else if(ad->wr_iot_control_users)--ad->wr_iot_control_users;
 else ad->wr_iot_control_poisoned=1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
}
#endif
