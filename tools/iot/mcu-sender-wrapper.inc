/* Candidate wrapper; adapter lifetime is pinned externally. The owner and
 * dedicated lock must be initialized before MCU publication and outlive it.
 * Internal transport owns msg after entry. A refused fresh msg is private.
 * Its destructor still accesses MCU counters: external adapter pin is required
 * even on admission refusal. Sender drain does not retire private builders.
 * This wrapper does not join asynchronous DMA or queue consumers. */
INT32 AndesSendCmdMsg(PRTMP_ADAPTER ad, struct cmd_msg *msg)
{
 ULONG flags=0;
 INT32 result;
 int entered,left,radio_control;
 if(!ad||!msg)return NDIS_STATUS_FAILURE;
 radio_control=msg->cmd_type==EXT_CID &&
               msg->ext_cmd_type==EXT_CMD_RADIO_ON_OFF_CTRL;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 entered=(!radio_control || !ad->wr_iot_mcu_sender_owner.radio_active) &&
         wr_iot_mcu_sender_enter(&ad->wr_iot_mcu_sender_owner);
 if(entered && radio_control)ad->wr_iot_mcu_sender_owner.radio_active=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 if(!entered){
  AndesForceFreeCmdMsg(msg);
  return NDIS_STATUS_FAILURE;
 }
 /* Legacy radio callbacks only log status. Use the existing bounded checked
  * receive/result path before ownership transfers to transport. This changes
  * status propagation, not sequence freshness or firmware epoch proof.
  * Init already disables retransmission; keep unexpected modes fail-closed. */
 if(radio_control)msg->wr_iot_checked=1;
 result=wr_iot_mcu_send_body(ad,msg);
 /* msg may already be freed or owned by a queue: never inspect it here. */
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 /* A failed legacy ON/OFF may still yield a delayed result. Quarantine
  * this owner rather than allow sequence reuse to turn it into a new ACK.
  * Recovery requires a separately proven firmware/drain epoch. */
 if(radio_control && result!=NDIS_STATUS_SUCCESS){
  ad->wr_iot_mcu_sender_owner.uncertain=1;
  ad->wr_iot_mcu_sender_owner.closed=1;
 }
 if(radio_control)ad->wr_iot_mcu_sender_owner.radio_active=0;
 left=wr_iot_mcu_sender_leave(&ad->wr_iot_mcu_sender_owner);
 /* Wake while the adapter-lifetime lock is held: once unlock exposes zero
  * inflight, this function must never touch adapter-owned storage again. */
 wake_up_all(&ad->wr_iot_mcu_sender_wait);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 return left?result:NDIS_STATUS_FAILURE;
}
