/* Historical main-open lease after hardware preparation. Retain resources. */
INT32 wr_iot_mcu_boot_loader_abort(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int owned,irq_stopped,dma_stopped;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 /* Failure can invalidate live context; compare the retained lease directly. */
 owned=ad->wr_iot_boot_active&&ad->wr_iot_boot_hw_state==2&&
       ticket->peer_serial==ad->wr_iot_boot_ticket.peer_serial&&
       ticket->radio_serial==ad->wr_iot_boot_ticket.radio_serial&&
       ticket->radio_epoch==ad->wr_iot_boot_ticket.radio_epoch&&
       ticket->close_serial==ad->wr_iot_boot_ticket.close_serial&&
       ticket->close_epoch==ad->wr_iot_boot_ticket.close_epoch;
 if(owned){
  ad->wr_iot_boot_hw_state=1;ad->wr_iot_boot_failed=1;
  ad->wr_iot_boot_frozen=1;
  RTMP_CLEAR_FLAG(ad,fRTMP_ADAPTER_MCU_SEND_IN_BAND_CMD);
  ad->wr_iot_boot_irq_unmask_state=1;ad->wr_iot_boot_dma_state=1;
  ad->wr_iot_boot_dma_stop_verified=0;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!owned)return NDIS_STATUS_FAILURE;
 irq_stopped=wr_iot_nettask_boot_irq_abort(ad)==NDIS_STATUS_SUCCESS;
 dma_stopped=wr_iot_mcu_boot_dma_stop_hw(ad)==NDIS_STATUS_SUCCESS;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ad->wr_iot_boot_irq_unmask_state=3;
 ad->wr_iot_boot_dma_state=ad->wr_iot_boot_dma_stop_verified?3:4;
 ad->wr_iot_boot_hw_state=3;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return irq_stopped&&dma_stopped?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
