/* Private bootstrap command admission only. Normal sender/data stay fenced. */
INT32 wr_iot_mcu_boot_thaw(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,ticket)&&ad->wr_iot_boot_frozen&&
       ad->wr_iot_boot_hw_state==2&&ad->wr_iot_boot_hw_stage==6&&
       ad->wr_iot_boot_ring_stage==4&&!ad->wr_iot_boot_ring_busy&&!ad->wr_iot_boot_ring_failed&&
       ad->wr_iot_boot_ctrl_state==2&&ad->wr_iot_boot_rx_state==2&&
       ad->wr_iot_boot_irq_state==2&&ad->wr_iot_boot_dma_state==2&&
       ad->wr_iot_boot_dma_saved_valid&&
       ad->wr_iot_boot_irq_unmask_state==2&&ad->wr_iot_boot_mcu_only&&
       ad->wr_iot_boot_epoch_done&&
       ad->wr_iot_boot_epoch_radio_serial==ticket->radio_serial&&
       ad->wr_iot_boot_epoch_radio_epoch==ticket->radio_epoch&&
       !ad->wr_iot_sequence.occupied&&!ad->wr_iot_sequence.poisoned&&
       !ad->wr_iot_sequence.quarantined&&!ad->wr_iot_sequence.retired&&
       !ad->wr_iot_sequence.cursor&&
       !ad->wr_iot_mcu_sender_owner.messages&&wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
       OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags)&&
       RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_START_UP)&&
       RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_INTERRUPT_ACTIVE)&&
       !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_SUSPEND);
 if(ready){
  RTMP_SET_FLAG(ad,fRTMP_ADAPTER_MCU_SEND_IN_BAND_CMD);
  ad->wr_iot_boot_frozen=0;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
