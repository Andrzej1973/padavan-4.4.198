/* Candidate wrapper; adapter lifetime is pinned externally. The owner and
 * dedicated lock must be initialized before MCU publication and outlive it.
 * Internal transport owns msg after entry. A refused fresh msg is private.
 * This wrapper does not join asynchronous DMA or queue consumers. */
INT32 AndesSendCmdMsg(PRTMP_ADAPTER ad, struct cmd_msg *msg)
{
 ULONG flags=0;
 INT32 result;
 int entered,left;
 if(!ad||!msg)return NDIS_STATUS_FAILURE;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 entered=wr_iot_mcu_sender_enter(&ad->wr_iot_mcu_sender_owner);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 if(!entered){
  AndesForceFreeCmdMsg(msg);
  return NDIS_STATUS_FAILURE;
 }
 result=wr_iot_mcu_send_body(ad,msg);
 /* msg may already be freed or owned by a queue: never inspect it here. */
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 left=wr_iot_mcu_sender_leave(&ad->wr_iot_mcu_sender_owner);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 wake_up_all(&ad->wr_iot_mcu_sender_wait);
 return left?result:NDIS_STATUS_FAILURE;
}
