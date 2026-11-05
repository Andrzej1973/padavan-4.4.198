/* Sole main-open owner. Stage is the last fully verified operation, never
 * permission to resume after a failed transaction. Caller pins adapter/dev. */
static int wr_iot_mcu_boot_ring_publish(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket,unsigned int stage)
{
 ULONG flags=0,owner_flags=0;int ready;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial)||
    !wr_iot_mcu_boot_frozen_owned(ad))return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,ticket)&&ad->wr_iot_boot_frozen&&
       ad->wr_iot_boot_ring_busy&&!ad->wr_iot_boot_ring_failed&&
       stage==ad->wr_iot_boot_ring_stage+1;
 if(ready)ad->wr_iot_boot_ring_stage=stage;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
INT32 wr_iot_mcu_boot_ring_transaction(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready,success=0;
 struct wr_iot_mcu_boot_ticket saved;
 if(!ad||!ticket||in_atomic()||irqs_disabled()||
    !wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_matches(ad,ticket)&&!ad->wr_iot_boot_ring_busy&&
       !ad->wr_iot_boot_ring_failed&&!ad->wr_iot_boot_ring_stage;
 if(ready)ad->wr_iot_boot_ring_busy=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
 if(wr_iot_mcu_boot_rom_quiesce(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_ring_publish(ad,ticket,1))goto done;
 if(wr_iot_mcu_boot_rx_refresh(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_ring_publish(ad,ticket,2))goto done;
 if(wr_iot_mcu_boot_control_retire(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_ring_publish(ad,ticket,3))goto done;
 if(wr_iot_mcu_boot_ring_rearm(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_ring_publish(ad,ticket,4))goto done;
 success=1;
done:
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 if(success&&(!wr_iot_mcu_boot_context_matches(ad,ticket)||
    !ad->wr_iot_boot_frozen||ad->wr_iot_boot_ring_stage!=4))success=0;
 if(!success){ad->wr_iot_boot_ring_failed=1;ad->wr_iot_boot_failed=1;}
 ad->wr_iot_boot_ring_busy=0;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return success?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
