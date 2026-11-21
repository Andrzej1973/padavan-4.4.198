/* One CLOSE executor pins adapter/ticket. No resource release is allowed on
 * data-only join or an uncertain OFF. This is not a firmware epoch receipt. */
BOOLEAN wr_iot_ap_release_after_join(RTMP_ADAPTER *pAd,
 const struct wr_iot_radio_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;
 int ready,already;
 if(!pAd||!ticket||in_atomic()||irqs_disabled())return FALSE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 ready=ticket->operation==WR_RADIO_CLOSE&&!ticket->reset_kind&&ticket->serial&&
       ticket->serial==pAd->wr_iot_transition.serial&&
       ticket->epoch==pAd->wr_iot_transition.epoch&&
       pAd->wr_iot_transition.busy==WR_RADIO_CLOSE&&
       pAd->wr_iot_transition.mt_radio_off_stage==4U&&
       pAd->wr_iot_transition.shutdown_stage==6U&&
       !RTMP_TEST_FLAG(pAd,fRTMP_ADAPTER_INTERRUPT_IN_USE);
 already=pAd->wr_iot_transition.ap_cleanup_serial==ticket->serial;
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,owner_flags);
 ready=ready&&!pAd->wr_iot_nettask_initializing&&
       pAd->wr_iot_nettask_joined&&pAd->wr_iot_nettask_data_joined&&
       !pAd->wr_iot_nettask_data_joining&&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner)&&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner);
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,owner_flags);
 RTMP_SPIN_LOCK_IRQSAVE(&pAd->wr_iot_mcu_sender_lock,&owner_flags);
 ready=ready&&pAd->wr_iot_mcu_sender_owner.off_done&&
       pAd->wr_iot_mcu_sender_owner.close_serial==ticket->serial&&
       wr_iot_mcu_sender_drained(&pAd->wr_iot_mcu_sender_owner)&&
       (pAd->wr_iot_mcu_sender_owner.release_claimed ?
        !pAd->wr_iot_mcu_sender_owner.messages :
        wr_iot_mcu_sender_release_claim(&pAd->wr_iot_mcu_sender_owner));
 RTMP_SPIN_UNLOCK_IRQRESTORE(&pAd->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 if(!ready)return FALSE;
 /* A zero message count alone is a snapshot. The claim above excludes
  * future private builders; now permanently exclude tasklet reinitialization.
  * If initialization raced the first observation, retain the claimed MCU
  * owner and all AP resources rather than releasing beneath it. */
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,owner_flags);
 ready=!pAd->wr_iot_nettask_initializing&&pAd->wr_iot_nettask_joined&&
       pAd->wr_iot_nettask_data_joined&&!pAd->wr_iot_nettask_data_joining&&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner)&&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner);
 if(ready)pAd->wr_iot_nettask_release_claimed=1;
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,owner_flags);
 if(!ready)return FALSE;
 if(already)return TRUE;
 IF_DEV_CONFIG_OPMODE_ON_AP(pAd){
  MeasureReqTabExit(pAd);
  TpcReqTabExit(pAd);
  AutoChBssTableDestroy(pAd);
  ChannelInfoDestroy(pAd);
  wr_iot_ap_release_resource_body(pAd);
 }
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 pAd->wr_iot_transition.ap_cleanup_serial=ticket->serial;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return TRUE;
}
