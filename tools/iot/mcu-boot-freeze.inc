/* Construction fence before ROM/RX retirement. No bus/firmware proof implied. */
static int wr_iot_mcu_boot_frozen_drained(RTMP_ADAPTER *ad)
{
 ULONG flags=0;int ready;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 ready=ad->wr_iot_boot_frozen && !ad->wr_iot_mcu_sender_owner.messages &&
       wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 return ready;
}
INT32 wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad)
{
 ULONG flags=0,owner_flags=0;int ready;
 if(!ad||!wr_iot_mcu_boot_peer_matches(ad,ad->wr_iot_boot_ticket.peer_serial))return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=ad->wr_iot_boot_frozen &&
       wr_iot_mcu_boot_context_matches(ad,&ad->wr_iot_boot_ticket) &&
       !ad->wr_iot_mcu_sender_owner.messages &&
       wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
INT32 wr_iot_mcu_boot_freeze(RTMP_ADAPTER *ad)
{
 ULONG flags=0,owner_flags=0;int ready;
 if(!ad||in_atomic()||irqs_disabled()||
    !wr_iot_mcu_boot_peer_matches(ad,ad->wr_iot_boot_ticket.peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,&ad->wr_iot_boot_ticket) &&
       !ad->wr_iot_mcu_sender_owner.inflight && !ad->wr_iot_mcu_sender_owner.radio_active;
 if(ready)ad->wr_iot_boot_frozen=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
 if(!wait_event_timeout(ad->wr_iot_mcu_sender_wait,
     wr_iot_mcu_boot_frozen_drained(ad),msecs_to_jiffies(5000)))return NDIS_STATUS_FAILURE;
 return wr_iot_mcu_boot_frozen_owned(ad)?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
