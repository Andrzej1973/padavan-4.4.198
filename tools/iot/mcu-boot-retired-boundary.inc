/* Source-level ROM/RX retirement boundary, before controller recreation.
 * Never clear occupied, poison or unresolved quarantine. No admission grant.
 * Silicon/runtime acceptance of this protocol remains separate evidence. */
static int wr_iot_mcu_boot_retired_boundary_ready(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *t)
{
 return wr_iot_mcu_boot_context_matches(ad,t)&&ad->wr_iot_boot_frozen&&
        ad->wr_iot_boot_hw_state==1&&ad->wr_iot_boot_hw_stage==1&&
        ad->wr_iot_boot_ring_stage==4&&!ad->wr_iot_boot_ring_busy&&!ad->wr_iot_boot_ring_failed&&
        !ad->wr_iot_boot_ctrl_state&&!ad->wr_iot_boot_rx_state&&!ad->wr_iot_boot_irq_state&&
        !ad->wr_iot_boot_dma_state&&!ad->wr_iot_boot_irq_unmask_state&&
        !ad->wr_iot_boot_epoch_done&&!ad->wr_iot_boot_mcu_only&&
        !OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags)&&
        ad->wr_iot_boot_rom_kind>=1&&ad->wr_iot_boot_rom_kind<=2&&
        ad->wr_iot_boot_rom_peer_serial==t->peer_serial&&
        ad->wr_iot_boot_rom_radio_serial==t->radio_serial&&
        ad->wr_iot_boot_rom_radio_epoch==t->radio_epoch&&
        !ad->wr_iot_mcu_sender_owner.messages&&wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
        !ad->wr_iot_sequence.occupied&&!ad->wr_iot_sequence.poisoned&&!ad->wr_iot_sequence.quarantined&&
        !(ad->wr_iot_sequence.retired&~0xfffeU)&&ad->wr_iot_sequence.cursor<=15&&
        !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_HALT_IN_PROGRESS);
}
INT32 wr_iot_mcu_boot_retired_boundary(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready;struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_retired_boundary_ready(ad,ticket);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready||!wr_iot_mcu_boot_pse_empty(ad)||
    !wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_retired_boundary_ready(ad,ticket);
 if(ready){
  ad->wr_iot_boot_epoch_retired_mask=ad->wr_iot_sequence.retired;
  ad->wr_iot_sequence.retired=0;ad->wr_iot_sequence.cursor=0;
  ad->wr_iot_boot_epoch_radio_serial=ticket->radio_serial;
  ad->wr_iot_boot_epoch_radio_epoch=ticket->radio_epoch;
  ad->wr_iot_boot_epoch_done=1;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
