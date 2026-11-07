/* Owner wrapper for isolated config; no normal startup/data admission grant.
 * Config owner pins lifetime; lock order matches owned command transport. */
static int wr_iot_mcu_config_timing_ready(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 return ad->wr_iot_boot_config_state==1&&ad->wr_iot_boot_config_task==current&&
  wr_iot_mcu_boot_config_ready(ad,ticket,0)&&
  !ad->wr_iot_mcu_sender_owner.inflight&&!ad->wr_iot_mcu_sender_owner.radio_active&&
  !ad->wr_iot_boot_config_unconfirmed&&
  !ad->wr_iot_config_slot_pending.ticket.active&&
  !ad->wr_iot_config_slot_pending.ticket.poisoned&&
  !ad->wr_iot_config_slot_pending.ticket.generation&&
  !ad->wr_iot_config_edca_pending.ticket.active&&
  !ad->wr_iot_config_edca_pending.ticket.poisoned&&
  !ad->wr_iot_config_edca_pending.ticket.generation;
}
INT32 wr_iot_mcu_config_slot_owned(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket,unsigned int expected)
{
 ULONG flags=0,owner_flags=0;int ready,result=0;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_config_timing_ready(ad,ticket);
 if(ready){
  result=wr_iot_config_slot_mmio(ad,expected);
  if(!result)ad->wr_iot_boot_failed=1;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return result?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
