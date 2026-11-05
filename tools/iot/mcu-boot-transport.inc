/* Isolated bootstrap transport. Caller pins adapter/netdev and owns main open.
 * Normal message admission and terminal release claims remain closed.
 * No reset of sequence quarantine, firmware epoch or tasklet gates occurs. */
static int wr_iot_mcu_boot_peer_matches(RTMP_ADAPTER *ad,unsigned long serial)
{
 int ready;
 NdisAcquireSpinLock(&ad->MacTabLock);
 ready=serial && ad->wr_iot_peer_open_owner.serial==serial &&
       ad->wr_iot_peer_open_owner.device==ad->net_dev &&
       ad->wr_iot_peer_open_owner.phase==WR_PEER_OPEN_CONFIG &&
       wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor);
 NdisReleaseSpinLock(&ad->MacTabLock);
 return ready;
}
/* transition lock -> sender lock, matching the existing checked close order. */
static int wr_iot_mcu_boot_matches(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *t)
{
 const struct wr_iot_mcu_boot_ticket *s=&ad->wr_iot_boot_ticket;
 return t && ad->wr_iot_boot_active && !ad->wr_iot_boot_failed &&
        t->peer_serial==s->peer_serial && t->radio_serial==s->radio_serial &&
        t->radio_epoch==s->radio_epoch && t->close_serial==s->close_serial &&
        t->close_epoch==s->close_epoch &&
        ad->wr_iot_transition.busy==WR_RADIO_START &&
        ad->wr_iot_transition.serial==t->radio_serial &&
        ad->wr_iot_transition.epoch==t->radio_epoch &&
        ad->wr_iot_transition.close_body_serial==t->close_serial &&
        ad->wr_iot_transition.close_body_epoch==t->close_epoch &&
        !ad->wr_iot_transition.retiring && !ad->wr_iot_transition.reset_pending &&
        !ad->wr_iot_transition.pm_suspending && !ad->wr_iot_transition.pm_suspended &&
        !ad->wr_iot_mcu_sender_owner.poisoned &&
        !ad->wr_iot_mcu_sender_owner.uncertain &&
        ad->wr_iot_mcu_sender_owner.closed &&
        ad->wr_iot_mcu_sender_owner.release_claimed &&
        ad->wr_iot_mcu_sender_owner.off_done &&
        ad->wr_iot_mcu_sender_owner.close_serial==t->close_serial;
}
INT32 wr_iot_mcu_boot_reserve(RTMP_ADAPTER *ad,unsigned long peer_serial,
 struct wr_iot_mcu_boot_ticket *out)
{
 ULONG flags=0,owner_flags=0;int ready;
 if(!ad||!out||!IS_MT7603(ad)||ad->chipCap.hif_type!=HIF_MT||in_atomic()||irqs_disabled()||
    !wr_iot_mcu_boot_peer_matches(ad,peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=!ad->wr_iot_boot_active && !ad->wr_iot_boot_failed &&
       !OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags) &&
       ad->wr_iot_transition.busy==WR_RADIO_START &&
       ad->wr_iot_transition.close_body_serial &&
       ad->wr_iot_transition.close_body_epoch &&
       ad->wr_iot_transition.close_body_epoch!=~0UL &&
       ad->wr_iot_transition.epoch==ad->wr_iot_transition.close_body_epoch+1 &&
       ad->wr_iot_transition.serial>ad->wr_iot_transition.close_body_serial &&
       ad->wr_iot_transition.retired_serial==ad->wr_iot_transition.close_body_serial &&
       ad->wr_iot_mcu_sender_owner.release_claimed &&
       ad->wr_iot_mcu_sender_owner.off_done &&
       !ad->wr_iot_mcu_sender_owner.messages &&
       ad->wr_iot_mcu_sender_owner.close_serial==ad->wr_iot_transition.close_body_serial &&
       wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner);
 if(ready){
  ad->wr_iot_boot_ticket.peer_serial=peer_serial;
  ad->wr_iot_boot_ticket.radio_serial=ad->wr_iot_transition.serial;
  ad->wr_iot_boot_ticket.radio_epoch=ad->wr_iot_transition.epoch;
  ad->wr_iot_boot_ticket.close_serial=ad->wr_iot_transition.close_body_serial;
  ad->wr_iot_boot_ticket.close_epoch=ad->wr_iot_transition.close_body_epoch;
  ad->wr_iot_boot_active=1;
  ready=wr_iot_mcu_boot_matches(ad,&ad->wr_iot_boot_ticket);
  if(ready)*out=ad->wr_iot_boot_ticket;
  else ad->wr_iot_boot_failed=1;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
struct cmd_msg *wr_iot_mcu_boot_alloc(RTMP_ADAPTER *ad,unsigned int length,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready;struct cmd_msg *msg;
 if(!ad||!ticket||length>MT_UPLOAD_FW_UNIT||in_atomic()||irqs_disabled()||
    !wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NULL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_matches(ad,ticket) && OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags);
 if(ready && ad->wr_iot_mcu_sender_owner.messages==~0U){
  ad->wr_iot_mcu_sender_owner.poisoned=1;ad->wr_iot_boot_failed=1;ready=0;
 }
 if(ready)ad->wr_iot_mcu_sender_owner.messages++;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NULL;
 msg=wr_iot_mcu_alloc_body(ad,length);
 if(!msg){wr_iot_mcu_message_drop(ad,0,0);return NULL;}
 msg->wr_iot_boot_peer_serial=ticket->peer_serial;
 msg->wr_iot_boot_radio_serial=ticket->radio_serial;
 msg->wr_iot_boot_epoch=ticket->radio_epoch;
 return msg;
}
/* Fresh private bootstrap message only; transport consumes it on every path. */
INT32 wr_iot_mcu_boot_send(RTMP_ADAPTER *ad,struct cmd_msg *msg,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready,left;INT32 result;
 if(!ad||!msg)return NDIS_STATUS_FAILURE;
 if(!ticket||in_atomic()||irqs_disabled()||
    !wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))goto refuse;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_matches(ad,ticket) && OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags) &&
       msg->wr_iot_boot_peer_serial==ticket->peer_serial &&
       msg->wr_iot_boot_radio_serial==ticket->radio_serial &&
       msg->wr_iot_boot_epoch==ticket->radio_epoch &&
       !ad->wr_iot_mcu_sender_owner.inflight &&
       !ad->wr_iot_mcu_sender_owner.radio_active &&
       !msg->need_retransmit &&
       ad->chipOps.pci_kick_out_cmd_msg==AndesMTPciKickOutCmdMsg &&
       ((wr_iot_mcu_boot_command(msg->cmd_type,msg->ext_cmd_type)&&msg->need_wait) ||
        (msg->cmd_type==MT_FW_SCATTER&&!msg->ext_cmd_type&&!msg->need_wait));
 if(ready){
  ad->wr_iot_mcu_sender_owner.inflight=1;
  ad->wr_iot_mcu_sender_owner.radio_active=1;
  msg->wr_iot_checked=msg->need_wait?1:0;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)goto refuse;
 result=wr_iot_mcu_send_body(ad,msg);
 /* msg is consumed: only adapter ownership may be inspected from here. */
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 if(result!=NDIS_STATUS_SUCCESS){
  ad->wr_iot_boot_failed=1;ad->wr_iot_mcu_sender_owner.uncertain=1;
 }
 ad->wr_iot_mcu_sender_owner.radio_active=0;
 left=wr_iot_mcu_sender_leave(&ad->wr_iot_mcu_sender_owner);
 wake_up_all(&ad->wr_iot_mcu_sender_wait);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 return left?result:NDIS_STATUS_FAILURE;
refuse:
 AndesForceFreeCmdMsg(msg);return NDIS_STATUS_FAILURE;
}
