/* Caller supplies a live adapter/MLME callback. No firmware or DMA token. */
#ifndef WR_IOT_RA2_GTK_REQUEST_KERNEL_H
#define WR_IOT_RA2_GTK_REQUEST_KERNEL_H
#include "assoc-generation-kernel.h"
#include "ra2-rekey-admission.h"
struct wr_iot_ra2_gtk_request_scope {
 unsigned int active,wcid,generation;
};
/* No lock spans crypto, timer cancellation, handshake sending or key install. */
static inline void wr_iot_ra2_gtk_control_leave(RTMP_ADAPTER *ad,int failed)
{
 ULONG flags=0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->wr_iot_ra2_key_active!=1)failed=1;
 else ad->wr_iot_ra2_key_active=0;
 if(failed)ad->wr_iot_control_poisoned=1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 wr_iot_control_leave(ad);
}
static inline int wr_iot_ra2_gtk_request_enter(RTMP_ADAPTER *ad,
 MLME_QUEUE_ELEM *event,MAC_TABLE_ENTRY *entry,
 struct wr_iot_ra2_gtk_request_scope *scope)
{
 ULONG flags=0;
 int admitted=0;
 NdisZeroMemory(scope,sizeof(*scope));
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!ad->wr_iot_ra2_key_active&&ad->ApCfg.BssidNum==3&&
    ad->ApCfg.BssidNum<=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0])){
  admitted=wr_iot_ra2_rekey_admit(&ad->wr_iot_driver_owner,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->net_dev,ad->ApCfg.MBSSID[2].wdev.if_dev,VIRTUAL_IF_NUM(ad),
   &ad->wr_iot_control_users,&ad->wr_iot_control_poisoned,
   ad->wr_iot_boot_active||ad->wr_iot_boot_failed||
   ad->wr_iot_close_owner.active||ad->wr_iot_closed_probe.active);
  if(admitted)ad->wr_iot_ra2_key_active=1;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!admitted)return 0;
 /* Refuse contention before any key/nonce/station mutation. This is an RX
  * key request, not a one-shot timeout callback that requires queue progress. */
 if(!wr_assoc_try_table_lock(ad)){
  wr_iot_ra2_gtk_control_leave(ad,0);return 0;
 }
 admitted=entry&&event&&event->MsgLen>=LENGTH_802_11&&
  MAC_ADDR_EQUAL(((PHEADER_802_11)event->Msg)->Addr1,ad->ApCfg.MBSSID[2].wdev.bssid)&&
  event->assoc_wcid<MAX_LEN_OF_MAC_TABLE&&
  entry==&ad->MacTab.Content[event->assoc_wcid]&&IS_ENTRY_CLIENT(entry)&&
  entry->func_tb_idx==2&&entry->wdev==&ad->ApCfg.MBSSID[2].wdev&&
  !ad->wr_iot_peer_delete_active&&
  !ad->wr_assoc_event_users[event->assoc_wcid]&&
  wr_assoc_event_entry_current(ad,event,entry);
 if(admitted)admitted=wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner);
 if(admitted){
  scope->wcid=event->assoc_wcid;scope->generation=event->assoc_gen;
  ad->wr_assoc_event_users[scope->wcid]=1;scope->active=1;
 }
 NdisReleaseSpinLock(&ad->MacTabLock);
 if(!admitted)wr_iot_ra2_gtk_control_leave(ad,0);
 return admitted;
}
static inline void wr_iot_ra2_gtk_request_leave(RTMP_ADAPTER *ad,
 struct wr_iot_ra2_gtk_request_scope *scope)
{
 int failed=0;
 if(!scope->active)return;
 NdisAcquireSpinLock(&ad->MacTabLock);
 if(scope->wcid>=MAX_LEN_OF_MAC_TABLE||
    ad->wr_assoc_event_users[scope->wcid]!=1||
    ad->MacTab.Content[scope->wcid].assoc_gen!=scope->generation)failed=1;
 else ad->wr_assoc_event_users[scope->wcid]=0;
 if(!wr_iot_peer_table_transaction_leave(&ad->wr_iot_peer_table_owner))failed=1;
 scope->active=0;
 NdisReleaseSpinLock(&ad->MacTabLock);
 wr_iot_ra2_gtk_control_leave(ad,failed);
}
#endif
