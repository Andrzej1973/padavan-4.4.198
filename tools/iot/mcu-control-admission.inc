/* transition_lock serializes these actors with bootstrap reservation.
 * No MMIO, sleeping or callbacks while held. Adapter lifetime is caller-owned.
 * This covers Linux ioctl and MLME periodic execution only, not all remap users. */
INT32 wr_iot_control_enter(RTMP_ADAPTER *ad)
{
 ULONG flags=0;int ready;
 if(!ad)return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ready=!ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&
       !ad->wr_iot_boot_failed&&!ad->wr_iot_transition.busy&&
       !ad->wr_iot_transition.retiring&&!ad->wr_iot_transition.reset_pending&&
       !ad->wr_iot_transition.pm_suspending&&!ad->wr_iot_transition.pm_suspended;
 if(ready){
  if(ad->wr_iot_control_users==~0U){ad->wr_iot_control_poisoned=1;ready=0;}
  else ad->wr_iot_control_users++;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
VOID wr_iot_control_leave(RTMP_ADAPTER *ad)
{
 ULONG flags=0;
 if(!ad)return;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->wr_iot_control_users)ad->wr_iot_control_users--;
 else ad->wr_iot_control_poisoned=1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
}
