/* Scheduler phase owns frozen constructors; no MMIO while these locks held.
 * State: 0 untouched, 1 claimed, 2 complete, 3 retained failure.
 * Integration must initialize state only at adapter allocation. */
INT32 wr_iot_mcu_boot_scheduler_claim(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,ticket)&&
       !ad->wr_iot_boot_scheduler_state&&!ad->wr_iot_boot_frozen&&
       ad->wr_iot_boot_hw_state==2&&ad->wr_iot_boot_hw_stage==6&&
       ad->wr_iot_boot_ctrl_state==2&&ad->wr_iot_boot_rx_state==2&&
       ad->wr_iot_boot_irq_state==2&&ad->wr_iot_boot_dma_state==2&&
       ad->wr_iot_boot_irq_unmask_state==2&&ad->wr_iot_boot_mcu_only&&
       ad->MCUCtrl.Stage==FW_RUN_TIME&&
       !ad->wr_iot_mcu_sender_owner.messages&&
       wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
       !ad->wr_iot_sequence.occupied&&!ad->wr_iot_sequence.poisoned&&
       !ad->wr_iot_sequence.quarantined&&
       !ad->bPCIclkOff&&
       !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|
          fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_SUSPEND);
 if(ready){ad->wr_iot_boot_scheduler_state=1;ad->wr_iot_boot_frozen=1;}
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
/* Call only after firmware-start completion; normal admission stays closed. */
INT32 wr_iot_mcu_boot_scheduler_run(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 struct wr_iot_mcu_boot_ticket saved;int success;
 if(!ad||!ticket)return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(wr_iot_mcu_boot_scheduler_claim(ad,ticket)!=NDIS_STATUS_SUCCESS)
  return NDIS_STATUS_FAILURE;
 success=wr_iot_mcu_boot_scheduler_check(ad)==NDIS_STATUS_SUCCESS;
 if(wr_iot_mcu_boot_scheduler_finish(ad,ticket,success)==NDIS_STATUS_SUCCESS)
  return NDIS_STATUS_SUCCESS;
 (void)wr_iot_mcu_boot_loader_abort(ad,ticket);
 return NDIS_STATUS_FAILURE;
}
INT32 wr_iot_mcu_boot_scheduler_owned(RTMP_ADAPTER *ad)
{
 ULONG flags=0,owner_flags=0;int ready;
 if(!ad||!wr_iot_mcu_boot_peer_matches(ad,ad->wr_iot_boot_ticket.peer_serial))return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,&ad->wr_iot_boot_ticket)&&
       ad->wr_iot_boot_scheduler_state==1&&ad->wr_iot_boot_frozen&&
       ad->wr_iot_boot_hw_state==2&&ad->wr_iot_boot_hw_stage==6&&
       ad->wr_iot_boot_ctrl_state==2&&ad->wr_iot_boot_rx_state==2&&
       ad->wr_iot_boot_irq_state==2&&ad->wr_iot_boot_dma_state==2&&
       ad->wr_iot_boot_irq_unmask_state==2&&ad->wr_iot_boot_mcu_only&&
       ad->MCUCtrl.Stage==FW_RUN_TIME&&!ad->bPCIclkOff&&
       !ad->wr_iot_mcu_sender_owner.messages&&
       wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
       !ad->wr_iot_sequence.occupied&&!ad->wr_iot_sequence.poisoned&&
       !ad->wr_iot_sequence.quarantined&&
       !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|
          fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_SUSPEND);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
INT32 wr_iot_mcu_boot_scheduler_finish(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket,int success)
{
 ULONG flags=0,owner_flags=0;int owned,ready,peer;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 peer=wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 owned=ad->wr_iot_boot_active&&ad->wr_iot_boot_scheduler_state==1&&
       ticket->peer_serial==ad->wr_iot_boot_ticket.peer_serial&&
       ticket->radio_serial==ad->wr_iot_boot_ticket.radio_serial&&
       ticket->radio_epoch==ad->wr_iot_boot_ticket.radio_epoch&&
       ticket->close_serial==ad->wr_iot_boot_ticket.close_serial&&
       ticket->close_epoch==ad->wr_iot_boot_ticket.close_epoch;
 ready=owned&&success&&peer&&wr_iot_mcu_boot_context_matches(ad,ticket)&&
       ad->wr_iot_boot_frozen&&!ad->wr_iot_mcu_sender_owner.messages&&
       wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
       !ad->wr_iot_sequence.occupied&&!ad->wr_iot_sequence.poisoned&&
       !ad->wr_iot_sequence.quarantined&&!ad->bPCIclkOff&&
       ad->wr_iot_boot_hw_state==2&&ad->wr_iot_boot_hw_stage==6&&
       ad->wr_iot_boot_ctrl_state==2&&ad->wr_iot_boot_rx_state==2&&
       ad->wr_iot_boot_irq_state==2&&ad->wr_iot_boot_dma_state==2&&
       ad->wr_iot_boot_irq_unmask_state==2&&ad->wr_iot_boot_mcu_only&&
       ad->MCUCtrl.Stage==FW_RUN_TIME&&
       !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|
          fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_SUSPEND);
 if(owned){
  ad->wr_iot_boot_scheduler_state=ready?2:3;
  if(!ready)ad->wr_iot_boot_failed=1;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 /* Historical loader-abort performs IRQ/DMA cleanup outside these locks. */
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
