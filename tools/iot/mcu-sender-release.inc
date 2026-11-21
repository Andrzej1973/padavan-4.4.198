/* Software gate only. External caller retirement and IRQ/DMA/queue teardown
 * must be proven by the surrounding adapter release protocol. No wait here:
 * preserve resources for a later retry if any invocation/message is live. */
INT wr_iot_mcu_sender_release_begin(RTMP_ADAPTER *ad)
{
 ULONG flags=0;
 unsigned long serial;
 int ready=0;
 if(!ad)return NDIS_STATUS_FAILURE;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 serial=ad->wr_iot_mcu_sender_owner.close_serial;
 if(!serial)serial=~0UL;
 if(ad->wr_iot_mcu_sender_owner.release_claimed){
  ready=wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
        !ad->wr_iot_mcu_sender_owner.messages;
 }else if(wr_iot_mcu_sender_close(&ad->wr_iot_mcu_sender_owner,serial)){
  ready=wr_iot_mcu_sender_release_claim(&ad->wr_iot_mcu_sender_owner);
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
