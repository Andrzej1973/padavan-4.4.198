/* CLOSE owner pins adapter/ticket. Normal sends remain closed after entry.
 * RX/IRQ must remain available until the checked transport returns. This
 * lease proves neither ACK freshness nor later DMA/IRQ retirement. */
static int wr_iot_mcu_off_ticket_current(RTMP_ADAPTER *ad,
 const struct wr_iot_radio_ticket *ticket)
{
 return ticket && ticket->operation==WR_RADIO_CLOSE && !ticket->reset_kind &&
        ticket->serial && ad->wr_iot_transition.busy==WR_RADIO_CLOSE &&
        ad->wr_iot_transition.serial==ticket->serial &&
        ad->wr_iot_transition.epoch==ticket->epoch &&
        ad->wr_iot_transition.mt_radio_off_stage==2U;
}
INT32 wr_iot_mcu_send_owned_off(RTMP_ADAPTER *ad,struct cmd_msg *msg,
 const struct wr_iot_radio_ticket *ticket)
{
 ULONG transition_flags=0,sender_flags=0;
 INT32 result;
 int valid,accepted=0,finished;
 if(!ad||!msg)return NDIS_STATUS_FAILURE;
 if(!ticket||in_atomic()||irqs_disabled()||!msg->need_wait||
    msg->need_retransmit||!msg->need_rsp||msg->cmd_type!=EXT_CID||
    msg->ext_cmd_type!=EXT_CMD_RADIO_ON_OFF_CTRL)goto refuse;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,transition_flags);
 valid=wr_iot_mcu_off_ticket_current(ad,ticket);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,transition_flags);
 if(!valid)goto refuse;
 if(wr_iot_mcu_sender_close_drain(ad,ticket->serial)!=NDIS_STATUS_SUCCESS)
  goto refuse;
 /* Lock order: transition, then sender. No wait/transport under either.
  * Revalidate after the unlocked sender drain before claiming OFF. */
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,transition_flags);
 if(wr_iot_mcu_off_ticket_current(ad,ticket)){
  RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&sender_flags);
  accepted=wr_iot_mcu_sender_off_begin(&ad->wr_iot_mcu_sender_owner,
                                      ticket->serial);
  RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&sender_flags);
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,transition_flags);
 if(!accepted)goto refuse;
 msg->wr_iot_checked=TRUE;
 result=wr_iot_mcu_send_body(ad,msg);
 /* Transport consumed msg. Only the pinned adapter and local result remain. */
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&sender_flags);
 finished=wr_iot_mcu_sender_off_finish(&ad->wr_iot_mcu_sender_owner,
                       ticket->serial,result==NDIS_STATUS_SUCCESS);
 wake_up_all(&ad->wr_iot_mcu_sender_wait);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&sender_flags);
 return finished?result:NDIS_STATUS_FAILURE;
refuse:
 /* No transfer occurred: the fresh builder message is still private. */
 AndesForceFreeCmdMsg(msg);
 return NDIS_STATUS_FAILURE;
}
