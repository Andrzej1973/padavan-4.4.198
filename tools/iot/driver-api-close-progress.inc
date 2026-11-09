/* Staged Linux-only progress operation, not a wire opcode or installed ioctl.
 * Caller owns RTNL and registration/adapter lifetime. All launch/reconcile
 * callers must share that serialization. Returns reference-retirement status
 * only; active OPEN/isolation fence remains. Never retries dev_close. */
static INT wr_iot_driver_close_progress(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *request)
{
 struct wr_iot_interface_ref *record;
 struct task_struct *handle;ULONG flags=0;int matched,transferred,designated,status;
 if(!ad||!dev||!request)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=wr_iot_driver_close_progress_matches(&ad->wr_iot_close_owner,
  &ad->wr_iot_driver_owner,dev,request);
 handle=(struct task_struct *)ad->wr_iot_close_owner.retirement_handle;
 transferred=ad->wr_iot_close_owner.retirement_module_transferred;
 designated=ad->wr_iot_close_owner.retirement_task!=NULL;
 if(matched&&transferred){
  record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,
   ad->wr_iot_close_owner.generation);
  /* Retained owner provenance is not a current-adapter receipt after reset. */
  matched=record&&
   record->close_prior_phase==(int)ad->wr_iot_close_owner.ticket.prior_phase&&
   record->close_prior_ready==ad->wr_iot_close_owner.ticket.prior_ready&&
   ad->wr_iot_transition.epoch==ad->wr_iot_close_owner.ticket.epoch&&
   !ad->wr_iot_transition.reset_pending&&!ad->wr_iot_transition.retiring&&
   !ad->wr_iot_transition.pm_suspending&&!ad->wr_iot_transition.pm_suspended&&
   !wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner)&&
   wr_iot_mbss_closed_reference(&ad->wr_iot_transition,ad->wr_iot_interface_refs,
    WDEV_NUM_MAX+1,ad->net_dev,dev,ad->wr_iot_close_owner.generation,
    ad->wr_iot_close_owner.open_token,ad->wr_iot_close_owner.ticket.serial,
    VIRTUAL_IF_NUM(ad));
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EBUSY;
 if(transferred)return 0;
 if(handle){
  /* Return only a completed refused task's tracked ref. Do not start another
   * task within this call; report EAGAIN for an explicit later progress call. */
  status=wr_iot_driver_close_retirement_reconcile(ad,&handle);
  return status?status:-EAGAIN;
 }
 if(designated)return -EINPROGRESS;
 status=wr_iot_driver_close_retirement_launch(ad,&handle);
 /* launch records any retained caller ref in close.retirement_handle; this
  * stack copy is never sole ownership storage on error. */
 return status?status:-EINPROGRESS;
}
