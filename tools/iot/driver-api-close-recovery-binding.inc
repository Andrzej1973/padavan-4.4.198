/* Staged adapter-bound scheduling of transferred API netdev ownership.
 * RTNL and active API owner fence pin adapter/registration throughout.
 * -1 refuses unchanged ownership, 0 accepted/scheduled, 1 accepted/retained.
 * Existing recovery worker/join owns the transferred dev_put; never acquire
 * another netdev reference here, or return accepted ownership to the caller. */
static INT wr_iot_driver_close_recovery_submit(RTMP_ADAPTER *ad,PNET_DEV dev)
{
 struct wr_iot_interface_ref *record;
 struct wr_iot_mbss_recovery_owner *owner;
 ULONG flags=0;unsigned int slot;int accepted=0,scheduled=0;
 if(!ad||!dev)return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_mbss_submission_enter(&ad->wr_iot_mbss_reaper_gate))goto out;
 if(!IS_MT7603(ad)||ad->ApCfg.BssidNum!=3||ad->net_dev==dev||
    ad->ApCfg.MBSSID[2].wdev.if_dev!=dev)goto leave;
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,
                            ad->wr_iot_close_owner.generation);
 if(!record||ad->wr_iot_transition.retiring)goto leave;
 slot=(unsigned int)(record-ad->wr_iot_interface_refs);
 if(work_busy(&ad->wr_iot_mbss_work[slot].work))goto leave;
 owner=&ad->wr_iot_mbss_recovery[slot];
 accepted=wr_iot_driver_close_transfer_recovery(&ad->wr_iot_close_owner,
  owner,record,&ad->wr_iot_transition);
 if(accepted){
  scheduled=schedule_work(&ad->wr_iot_mbss_work[slot].work);
  if(!scheduled)owner->phase=WR_MBSS_OWNER_RETAINED;
 }
leave:
 (void)wr_iot_mbss_submission_leave(&ad->wr_iot_mbss_reaper_gate);
out:
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return accepted?(scheduled?0:1):-1;
}
