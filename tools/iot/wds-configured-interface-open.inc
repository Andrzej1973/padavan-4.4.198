/* Called after the exact WDS interface became OWNED, before queue/HNAT start.
 * Main physical startup must not wait for administratively closed WDS links.
 * Caller retains module/adapter/netdev lifetime across this synchronous call. */
BOOLEAN wr_iot_wds_configured_interface_open(RTMP_ADAPTER *pAd,PNET_DEV device,
 unsigned long generation)
{
 UINT index;
 ULONG flags;
 BOOLEAN valid=FALSE,configured=FALSE;
 if(!pAd||!device||!generation)return FALSE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 for(index=0;index<MAX_WDS_ENTRY;index++){
  struct wr_iot_interface_ref *record;
  if(pAd->WdsTab.WdsEntry[index].wdev.if_dev!=device)continue;
  record=wr_iot_registry_find(pAd->wr_iot_interface_refs,WDEV_NUM_MAX+1,device,generation);
  valid=record&&record->published&&!record->removing&&record->family==WR_REF_FAMILY_WDS&&
   record->phase==WR_REF_OWNED&&!pAd->wr_iot_transition.retiring&&
   !pAd->wr_iot_transition.pm_suspending&&!pAd->wr_iot_transition.pm_suspended;
  configured=pAd->WdsTab.WdsEntry[index].Valid==TRUE;
  break;
 }
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 if(!valid)return FALSE;
 if(!configured)return TRUE; /* Lazy/unconfigured interface: no invented peer. */
 return wr_iot_wds_insert_transaction_identity(pAd,
  pAd->WdsTab.WdsEntry[index].PeerWdsAddr,index,2,NULL,0,device,generation)!=NULL;
}
