/* Configuration ownership only: no normal MCU/data admission or hardware grant.
 * Keep a task reference until its historical ticket is explicitly finished. */
static int wr_iot_mcu_boot_config_ready(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *t)
{
 return wr_iot_mcu_boot_context_matches(ad,t)&&ad->wr_iot_boot_frozen&&
  ad->wr_iot_boot_fw_state==2&&ad->wr_iot_boot_scheduler_state==2&&
  ad->wr_iot_boot_fw_radio_serial==t->radio_serial&&
  ad->wr_iot_boot_fw_radio_epoch==t->radio_epoch&&
  ad->wr_iot_boot_hw_state==2&&ad->wr_iot_boot_hw_stage==6&&
  ad->wr_iot_boot_ctrl_state==2&&ad->wr_iot_boot_rx_state==2&&
  ad->wr_iot_boot_irq_state==2&&ad->wr_iot_boot_dma_state==2&&
  ad->wr_iot_boot_irq_unmask_state==2&&ad->wr_iot_boot_mcu_only&&
  ad->MCUCtrl.Stage==FW_RUN_TIME&&!ad->bPCIclkOff&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_mcu_sender_owner.messages&&
  wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
  !ad->wr_iot_sequence.occupied&&!ad->wr_iot_sequence.poisoned&&
  !ad->wr_iot_sequence.quarantined&&!ad->wr_iot_sequence.retired&&
  !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|
     fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_SUSPEND);
}
INT32 wr_iot_mcu_boot_config_begin(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 get_task_struct(current);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=!ad->wr_iot_boot_config_state&&!ad->wr_iot_boot_config_task&&
       wr_iot_mcu_boot_config_ready(ad,ticket);
 if(ready){ad->wr_iot_boot_config_task=current;ad->wr_iot_boot_config_state=1;}
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)put_task_struct(current);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
INT32 wr_iot_mcu_boot_config_finish(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket,int success)
{
 ULONG flags=0,owner_flags=0;int owned,ready,peer;
 struct wr_iot_mcu_boot_ticket saved;struct task_struct *task=NULL;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 peer=wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 owned=ad->wr_iot_boot_active&&ad->wr_iot_boot_config_state==1&&
  ad->wr_iot_boot_config_task==current&&
  ticket->peer_serial==ad->wr_iot_boot_ticket.peer_serial&&
  ticket->radio_serial==ad->wr_iot_boot_ticket.radio_serial&&
  ticket->radio_epoch==ad->wr_iot_boot_ticket.radio_epoch&&
  ticket->close_serial==ad->wr_iot_boot_ticket.close_serial&&
  ticket->close_epoch==ad->wr_iot_boot_ticket.close_epoch;
 ready=owned&&success&&peer&&wr_iot_mcu_boot_config_ready(ad,ticket);
 if(owned){
  ad->wr_iot_boot_config_state=ready?2:3;
  if(!ready)ad->wr_iot_boot_failed=1;
  task=ad->wr_iot_boot_config_task;ad->wr_iot_boot_config_task=NULL;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(task)put_task_struct(task);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
