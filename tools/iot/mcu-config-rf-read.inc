/* Read only the outstanding owned RF intent. ACK storage stays in msg;
 * caller output is written synchronously after checked send/drain/retirement. */
INT32 wr_iot_mcu_config_rf_read(RTMP_ADAPTER *ad,UINT32 stream,UINT32 address,UINT32 *value)
{
 ULONG flags=0,owner_flags=0;int ready;INT32 result;
 struct wr_iot_config_rf_pending saved;
 struct cmd_msg *msg;UINT32 request[3];
 if(!ad||!value||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 saved=ad->wr_iot_config_rf_pending;
 ready=ad->wr_iot_boot_config_state==1&&ad->wr_iot_boot_config_task==current&&
  wr_iot_mcu_boot_config_ready(ad,&ad->wr_iot_boot_ticket,0)&&
  ad->wr_iot_boot_config_unconfirmed&&
  wr_iot_config_rf_record_matches(&saved,saved.generation,
   ad->wr_iot_boot_ticket.peer_serial,ad->wr_iot_boot_ticket.radio_serial,
   ad->wr_iot_boot_ticket.radio_epoch,ad->wr_iot_boot_ticket.close_serial,
   ad->wr_iot_boot_ticket.close_epoch,stream,address,saved.value);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
 msg=wr_iot_mcu_config_alloc(ad,12);
 if(!msg)return NDIS_STATUS_RESOURCES;
 AndesInitCmdMsg(msg,P1_Q0,EXT_CID,CMD_QUERY,EXT_CMD_RF_REG_ACCESS,
  TRUE,0,FALSE,TRUE,12,NULL,NULL);
 msg->wr_iot_config_rf_query=1;msg->wr_iot_config_rf_generation=saved.generation;
 msg->wr_iot_config_rf_stream=saved.stream;msg->wr_iot_config_rf_address=saved.address;
 msg->wr_iot_config_rf_value=saved.value;
 request[0]=cpu2le32(stream);request[1]=cpu2le32(address);request[2]=0;
 AndesAppendCmdMsg(msg,(char *)request,sizeof(request));
 result=wr_iot_mcu_config_send(ad,msg);
 if(result==NDIS_STATUS_SUCCESS)*value=saved.value;
 return result;
}
