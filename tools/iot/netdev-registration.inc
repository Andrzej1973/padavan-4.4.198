/* Candidate attach bridge. Caller pins adapter/device and serializes attach
 * vs unregister. Registry exists before kernel publication. No lock over RTNL. */
static enum wr_iot_ref_family wr_iot_hook_family(int priv_flags)
{
 switch(priv_flags){
 case INT_MAIN:return WR_REF_FAMILY_MAIN;
 case INT_MBSSID:return WR_REF_FAMILY_MBSS;
 case INT_APCLI:return WR_REF_FAMILY_APCLI;
 case INT_WDS:return WR_REF_FAMILY_WDS;
 case INT_MONITOR:return WR_REF_FAMILY_MONITOR;
 default:return WR_REF_FAMILY_UNKNOWN;
 }
}
INT wr_iot_netdev_attach_checked(RTMP_ADAPTER *pAd, UCHAR mode,
 PNET_DEV dev, RTMP_OS_NETDEV_OP_HOOK *hook)
{
 struct wr_iot_interface_ref *record;
 unsigned long generation;
 ULONG flags;
 INT status;
 int last_registration;
 int mbss;
 enum wr_iot_ref_family family;
 unsigned int bss_idx=0;
 if(!pAd||!dev||!hook)return NDIS_STATUS_FAILURE;
 family=wr_iot_hook_family(hook->priv_flags);
 if(family==WR_REF_FAMILY_UNKNOWN)return NDIS_STATUS_FAILURE;
 mbss=hook->priv_flags==INT_MBSSID;
 if(mbss){
  struct wifi_dev *wdev=(struct wifi_dev *)hook->wdev;
  if(!wdev||wdev->func_idx>=WDEV_NUM_MAX)return NDIS_STATUS_FAILURE;
  bss_idx=wdev->func_idx;
 }
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 if(pAd->wr_iot_transition.retiring||pAd->wr_iot_transition.pm_suspending||
    pAd->wr_iot_transition.pm_suspended||
    pAd->wr_iot_transition.phase==WR_RADIO_CLOSING||
    pAd->wr_iot_registration_inflight==~0U){
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }
 record=wr_iot_registry_add_family(pAd->wr_iot_interface_refs,WDEV_NUM_MAX+1,
                           &pAd->wr_iot_registration_generation,dev,family);
 generation=record?record->generation:0;
 if(record&&mbss&&!wr_bss_retirement_publish(
    &pAd->wr_iot_mbss[bss_idx],generation)){
  wr_iot_registry_release(record,dev,generation);
  record=NULL;
 }
 if(record)pAd->wr_iot_registration_inflight++;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 if(!record)return NDIS_STATUS_FAILURE;
 status=RtmpOSNetDevAttach(mode,dev,hook);
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 if(status!=NDIS_STATUS_SUCCESS){
  /* Failed register did not publish an administratively opened interface.
   * Caller owns failed construction and must still free vendor allocations. */
  wr_iot_registry_release(record,dev,generation);
  if(mbss&&pAd->wr_iot_mbss[bss_idx].generation==generation&&
     pAd->wr_iot_mbss[bss_idx].stage==WR_BSS_LIVE)
   wr_bss_retirement_init(&pAd->wr_iot_mbss[bss_idx]);
 }else{
  record->published=1;
 }
 pAd->wr_iot_registration_inflight--;
 last_registration=pAd->wr_iot_registration_inflight==0;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 if(last_registration)wake_up_all(&pAd->wr_iot_registration_wait);
 return status;
}

/* Admission barrier only. Caller must invoke before unregister and finish
 * kernel/vendor quiescence before releasing this slot for reuse. */
INT wr_iot_netdev_mark_removing(RTMP_ADAPTER *pAd, PNET_DEV dev)
{
 struct wr_iot_interface_ref *record=NULL;
 unsigned int i;
 ULONG flags;
 INT status=NDIS_STATUS_FAILURE;
 if(!pAd||!dev)return status;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 for(i=0;i<WDEV_NUM_MAX+1;i++)
  if(pAd->wr_iot_interface_refs[i].device==dev){
   record=&pAd->wr_iot_interface_refs[i];break;
  }
 if(record&&record->published&&!record->removing&&
    wr_iot_registry_begin_remove(record,dev,record->generation))
  status=NDIS_STATUS_SUCCESS;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return status;
}

/* Use only when the attempted removal made no vendor/kernel mutation.
 * Caller retains adapter/device lifetime. The shared lock makes the PM
 * fence and the mark cancellation one atomic decision. */
INT wr_iot_netdev_cancel_removing_unmutated(RTMP_ADAPTER *pAd, PNET_DEV dev)
{
 struct wr_iot_interface_ref *record=NULL;
 unsigned int i;
 ULONG flags;
 INT status=NDIS_STATUS_FAILURE;
 if(!pAd||!dev)return status;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 for(i=0;i<WDEV_NUM_MAX+1;i++)
  if(pAd->wr_iot_interface_refs[i].device==dev){
   record=&pAd->wr_iot_interface_refs[i];break;
  }
 if(record&&wr_iot_registry_cancel_remove_unmutated(record,dev,
    record->generation,pAd->wr_iot_transition.pm_suspending||
    pAd->wr_iot_transition.pm_suspended||pAd->wr_iot_transition.retiring))
  status=NDIS_STATUS_SUCCESS;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return status;
}

/* MBSS removal milestones share the registry lock and generation. These
 * helpers record caller-proven steps; they do not retire vendor callbacks. */
INT wr_iot_mbss_begin_remove(RTMP_ADAPTER *pAd, UINT bss, PNET_DEV dev)
{
 struct wr_iot_interface_ref *record=NULL;
 struct wr_bss_retirement *state;
 unsigned int i;
 ULONG flags;
 INT status=NDIS_STATUS_FAILURE;
 if(!pAd||!dev||bss>=WDEV_NUM_MAX)return status;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 state=&pAd->wr_iot_mbss[bss];
 if(pAd->wr_iot_transition.pm_suspending||
    pAd->wr_iot_transition.pm_suspended||
    (!pAd->wr_iot_transition.retiring&&
     pAd->wr_iot_transition.busy!=WR_RADIO_BSS_CLOSE))goto out;
 for(i=0;i<WDEV_NUM_MAX+1;i++)
  if(pAd->wr_iot_interface_refs[i].device==dev){
   record=&pAd->wr_iot_interface_refs[i];break;
  }
 /* Detach must not race an administratively owned/open interface or an
  * admitted OS TX entry. The checked ndo_stop binding is still pending. */
 if(!record||!record->published||state->generation!=record->generation||
    record->phase!=WR_REF_IDLE||pAd->wr_iot_transition.active_tx||
    (record->last_token&&!record->open_unmutated&&
     record->close_stage!=4U))
  goto out;
 if(state->stage==WR_BSS_REMOVING&&record->removing){
  status=NDIS_STATUS_SUCCESS;goto out;
 }
 if(state->stage==WR_BSS_LIVE&&!record->removing&&
    wr_bss_retirement_begin(state,record->generation,1)){
  if(wr_iot_registry_begin_remove(record,dev,record->generation))
   status=NDIS_STATUS_SUCCESS;
  else
   wr_bss_retirement_abort_unmutated(state,record->generation,1);
 }
out:
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return status;
}

INT wr_iot_mbss_beacon_done(RTMP_ADAPTER *pAd, UINT bss, PNET_DEV dev)
{
 unsigned int i;
 ULONG flags;
 INT status=NDIS_STATUS_FAILURE;
 if(!pAd||!dev||bss>=WDEV_NUM_MAX)return status;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 for(i=0;i<WDEV_NUM_MAX+1;i++)
  if(pAd->wr_iot_interface_refs[i].device==dev&&
     pAd->wr_iot_interface_refs[i].removing&&
     wr_bss_retirement_beacon_done(&pAd->wr_iot_mbss[bss],
       pAd->wr_iot_interface_refs[i].generation)){
   status=NDIS_STATUS_SUCCESS;break;
  }
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return status;
}

INT wr_iot_mbss_cancel_unmutated(RTMP_ADAPTER *pAd, UINT bss, PNET_DEV dev)
{
 unsigned int i;
 ULONG flags;
 INT status=NDIS_STATUS_FAILURE;
 if(!pAd||!dev||bss>=WDEV_NUM_MAX)return status;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 for(i=0;i<WDEV_NUM_MAX+1;i++){
  struct wr_iot_interface_ref *r=&pAd->wr_iot_interface_refs[i];
  struct wr_bss_retirement *s=&pAd->wr_iot_mbss[bss];
  if(r->device==dev&&s->generation==r->generation&&
     s->stage==WR_BSS_REMOVING&&
     wr_iot_registry_cancel_remove_unmutated(r,dev,r->generation,
       pAd->wr_iot_transition.pm_suspending||
       pAd->wr_iot_transition.pm_suspended||
       pAd->wr_iot_transition.retiring)){
   wr_bss_retirement_abort_unmutated(s,r->generation,1);
   status=NDIS_STATUS_SUCCESS;break;
  }
 }
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return status;
}
