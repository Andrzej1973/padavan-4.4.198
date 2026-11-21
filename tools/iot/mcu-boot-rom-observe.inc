/* Method1 calls only after its checked restart result and ROM-ready loop.
 * This records provenance, not an epoch grant or permission to reset IDs. */
static int wr_iot_mcu_boot_rom_can_observe(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 return wr_iot_mcu_boot_matches(ad,ticket)&&!ad->wr_iot_boot_rom_kind&&
        !ad->wr_iot_boot_hw_state&&!ad->wr_iot_boot_hw_stage&&
        !ad->wr_iot_boot_ring_stage&&!ad->wr_iot_boot_ring_busy&&
        ad->wr_iot_boot_mcu_only&&OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags)&&
        !ad->wr_iot_mcu_sender_owner.messages&&wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
        !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_HALT_IN_PROGRESS);
}
INT32 wr_iot_mcu_boot_rom_observe(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket,unsigned int restart_acked)
{
 ULONG flags=0,owner_flags=0;UINT32 value;unsigned int sample;int ready;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||restart_acked>1||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_rom_can_observe(ad,ticket);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
 for(sample=0;sample<2;sample++){
  if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_HALT_IN_PROGRESS))return NDIS_STATUS_FAILURE;
  RTMP_IO_READ32(ad,0x1134U,&value); /* SDK TOP_MISC2 is private to andes_mt.c. */
  if(value==~(UINT32)0||(value&3U)!=1U)return NDIS_STATUS_FAILURE;
  if(!sample)RtmpusecDelay(1000);
 }
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_rom_can_observe(ad,ticket);
 if(ready){
  ad->wr_iot_boot_rom_kind=restart_acked?2:1;
  ad->wr_iot_boot_rom_peer_serial=ticket->peer_serial;
  ad->wr_iot_boot_rom_radio_serial=ticket->radio_serial;
  ad->wr_iot_boot_rom_radio_epoch=ticket->radio_epoch;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
