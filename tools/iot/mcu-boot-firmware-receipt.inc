/* Method1 invokes only after successful checked FW_START and valid RUN read.
 * Commit software provenance, not normal admission or device acceptance. */
INT32 wr_iot_mcu_boot_firmware_receipt(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,ticket)&&!ad->wr_iot_boot_fw_state&&
       !ad->wr_iot_boot_failed&&!ad->wr_iot_boot_frozen&&!ad->bPCIclkOff&&
       ad->wr_iot_boot_hw_state==2&&ad->wr_iot_boot_hw_stage==6&&
       ad->wr_iot_boot_ctrl_state==2&&ad->wr_iot_boot_rx_state==2&&
       ad->wr_iot_boot_irq_state==2&&ad->wr_iot_boot_dma_state==2&&
       ad->wr_iot_boot_irq_unmask_state==2&&ad->wr_iot_boot_mcu_only&&
       ad->MCUCtrl.Stage==FW_RUN_TIME&&ad->wr_iot_boot_epoch_done&&
       ad->wr_iot_boot_epoch_radio_serial==ticket->radio_serial&&
       ad->wr_iot_boot_epoch_radio_epoch==ticket->radio_epoch&&
       !ad->wr_iot_mcu_sender_owner.messages&&
       wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
       !ad->wr_iot_sequence.occupied&&!ad->wr_iot_sequence.poisoned&&
       !ad->wr_iot_sequence.quarantined&&
       !(ad->wr_iot_sequence.retired&~0xfffeU)&&ad->wr_iot_sequence.cursor<=15&&
       !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|
          fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_SUSPEND);
 if(ready){
  ad->wr_iot_boot_fw_retired=ad->wr_iot_sequence.retired;
  ad->wr_iot_boot_fw_cursor=ad->wr_iot_sequence.cursor;
  ad->wr_iot_boot_fw_radio_serial=ticket->radio_serial;
  ad->wr_iot_boot_fw_radio_epoch=ticket->radio_epoch;
  /* No later private restart/scatter may invalidate this receipt. */
  ad->wr_iot_boot_frozen=1;
  ad->wr_iot_boot_fw_state=2;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
