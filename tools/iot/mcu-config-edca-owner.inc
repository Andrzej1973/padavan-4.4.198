/* Include after shared timing readiness. Partial MMIO failure is permanent
 * for this config owner; never reopen admission or clear firmware journals. */
INT32 wr_iot_mcu_config_edca_owned(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket,const unsigned char *data,unsigned int length)
{
 ULONG flags=0,owner_flags=0;int ready,result=0;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||!data||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_config_timing_ready(ad,ticket);
 if(ready){
  result=wr_iot_config_edca_mmio(ad,data,length);
  if(!result)ad->wr_iot_boot_failed=1;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return result?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
