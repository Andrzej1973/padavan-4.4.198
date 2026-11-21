/* One synchronous checked multi-register write at a time. Normal sender stays
 * closed. Constructor and sender lifetimes use the existing message counters. */
struct cmd_msg *wr_iot_mcu_config_alloc(RTMP_ADAPTER *ad,unsigned int length)
{
 ULONG flags=0,owner_flags=0;int ready;struct cmd_msg *msg;
 struct wr_iot_mcu_boot_ticket ticket;
 if(!ad||!length||length>MT_UPLOAD_FW_UNIT||in_atomic()||irqs_disabled())return NULL;
 ticket=ad->wr_iot_boot_ticket;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket.peer_serial))return NULL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=ad->wr_iot_boot_config_state==1&&ad->wr_iot_boot_config_task==current&&
       wr_iot_mcu_boot_config_ready(ad,&ticket,0);
 if(ready)ad->wr_iot_mcu_sender_owner.messages++;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NULL;
 msg=wr_iot_mcu_alloc_body(ad,length);
 if(!msg){
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
  if(ad->wr_iot_boot_config_state==1&&ad->wr_iot_boot_config_task==current&&
     wr_iot_mcu_boot_context_matches(ad,&ticket))ad->wr_iot_boot_failed=1;
  RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  wr_iot_mcu_message_drop(ad,0,0);return NULL;
 }
 msg->wr_iot_config_owned=1;
 msg->wr_iot_config_peer_serial=ticket.peer_serial;
 msg->wr_iot_config_radio_serial=ticket.radio_serial;
 msg->wr_iot_config_radio_epoch=ticket.radio_epoch;
 msg->wr_iot_config_close_serial=ticket.close_serial;
 msg->wr_iot_config_close_epoch=ticket.close_epoch;
 return msg;
}
static int wr_iot_mcu_config_messages_gone(RTMP_ADAPTER *ad)
{
 ULONG flags=0;int gone;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 gone=!ad->wr_iot_mcu_sender_owner.messages;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 return gone;
}
INT32 wr_iot_mcu_config_send(RTMP_ADAPTER *ad,struct cmd_msg *msg)
{
 ULONG flags=0,owner_flags=0;int ready,left;INT32 result;
 struct wr_iot_mcu_boot_ticket ticket;
 if(!ad||!msg)return NDIS_STATUS_FAILURE;
 if(msg->priv!=ad||!msg->wr_iot_config_owned||in_atomic()||irqs_disabled())goto refuse;
 ticket.peer_serial=msg->wr_iot_config_peer_serial;
 ticket.radio_serial=msg->wr_iot_config_radio_serial;
 ticket.radio_epoch=msg->wr_iot_config_radio_epoch;
 ticket.close_serial=msg->wr_iot_config_close_serial;
 ticket.close_epoch=msg->wr_iot_config_close_epoch;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket.peer_serial))goto refuse;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=ad->wr_iot_boot_config_state==1&&ad->wr_iot_boot_config_task==current&&
       wr_iot_mcu_boot_config_ready(ad,&ticket,1)&&
       !ad->wr_iot_mcu_sender_owner.inflight&&!ad->wr_iot_mcu_sender_owner.radio_active&&
       msg->cmd_type==EXT_CID&&msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS&&
       msg->set_query==CMD_SET&&msg->need_wait&&msg->need_rsp&&!msg->need_retransmit&&
       msg->rsp_payload_len==WR_IOT_CONFIG_MULTI_WRITE_SIZE&&
       ad->chipOps.pci_kick_out_cmd_msg==AndesMTPciKickOutCmdMsg;
 if(ready){
  ad->wr_iot_mcu_sender_owner.inflight=1;ad->wr_iot_mcu_sender_owner.radio_active=1;
  msg->wr_iot_checked=1;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)goto refuse;
 result=wr_iot_mcu_send_body(ad,msg);
 /* Transport consumed msg. Inspect only adapter state after this point. */
 if(result==NDIS_STATUS_SUCCESS&&
    !wait_event_timeout(ad->wr_iot_mcu_sender_wait,
      wr_iot_mcu_config_messages_gone(ad),msecs_to_jiffies(5000)))
  result=NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ad->wr_iot_mcu_sender_owner.radio_active=0;
 left=wr_iot_mcu_sender_leave(&ad->wr_iot_mcu_sender_owner);
 if(result==NDIS_STATUS_SUCCESS&&(!left||ad->wr_iot_boot_config_state!=1||
    ad->wr_iot_boot_config_task!=current||!wr_iot_mcu_boot_config_ready(ad,&ticket,0)))
  result=NDIS_STATUS_FAILURE;
 if(result!=NDIS_STATUS_SUCCESS){ad->wr_iot_boot_failed=1;ad->wr_iot_mcu_sender_owner.uncertain=1;}
 wake_up_all(&ad->wr_iot_mcu_sender_wait);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return left?result:NDIS_STATUS_FAILURE;
refuse:
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 if(ad->wr_iot_boot_config_state==1&&msg->priv==ad&&msg->wr_iot_config_owned&&
    msg->wr_iot_config_peer_serial==ad->wr_iot_boot_ticket.peer_serial&&
    msg->wr_iot_config_radio_serial==ad->wr_iot_boot_ticket.radio_serial&&
    msg->wr_iot_config_radio_epoch==ad->wr_iot_boot_ticket.radio_epoch&&
    msg->wr_iot_config_close_serial==ad->wr_iot_boot_ticket.close_serial&&
    msg->wr_iot_config_close_epoch==ad->wr_iot_boot_ticket.close_epoch)
  ad->wr_iot_boot_failed=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 AndesForceFreeCmdMsg(msg);return NDIS_STATUS_FAILURE;
}
