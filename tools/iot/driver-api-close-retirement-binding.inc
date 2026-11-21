/* Caller holds transition lock and pins adapter/registration. No sleeping or
 * reference operations. A positive result is valid only under this lock;
 * future task designation/ownership transfer must occur before unlocking. */
static INT wr_iot_driver_close_retirement_ready_locked(RTMP_ADAPTER *ad)
{
 unsigned int slot;
 if(!ad||!IS_MT7603(ad)||ad->ApCfg.BssidNum!=3||
    ad->ApCfg.MBSSID[2].wdev.if_dev!=ad->wr_iot_close_owner.device||
    ad->wr_iot_main_recovery.deferred_owners||
    work_busy(&ad->wr_iot_main_recovery_work)||
    work_busy(&ad->wr_iot_main_recovery_reap_work.work)||
    work_busy(&ad->wr_iot_mbss_poll_work.work))return 0;
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++)
  if(work_busy(&ad->wr_iot_mbss_work[slot].work))return 0;
 return wr_iot_driver_close_retirement_ready(&ad->wr_iot_close_owner,
  &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  ad->net_dev,VIRTUAL_IF_NUM(ad),ad->wr_iot_mbss_recovery,WDEV_NUM_MAX+1,
  &ad->wr_iot_mbss_poll_state,&ad->wr_iot_mbss_reaper_gate,1);
}

/* The caller created this task stopped and owns its lifetime. Publish the
 * designation before wake, under the SAME lock as readiness validation.
 * No module-reference transfer occurs here; failures keep API ownership. */
static INT wr_iot_driver_close_retirement_designate_locked(RTMP_ADAPTER *ad,
 const void *stopped_task)
{
 if(!ad||!stopped_task||ad->wr_iot_close_owner.retirement_task||ad->wr_iot_close_owner.retirement_handle||
    ad->wr_iot_close_owner.retirement_started||ad->wr_iot_close_owner.retirement_canceling||
    ad->wr_iot_close_owner.retirement_entered||
    !wr_iot_driver_close_retirement_ready_locked(ad))return 0;
 ad->wr_iot_close_owner.retirement_task=stopped_task;
 ad->wr_iot_close_owner.retirement_error=0;
 return 1;
}
