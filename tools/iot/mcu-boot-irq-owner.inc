/* IRQ preparation does not enable interrupts, thaw constructors or reset IDs. */
INT32 wr_iot_mcu_boot_irq_prepare_owned(RTMP_ADAPTER *ad)
{
 ULONG flags=0,owner_flags=0;int ready;
 if(!ad||!wr_iot_mcu_boot_peer_matches(ad,ad->wr_iot_boot_ticket.peer_serial))return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,&ad->wr_iot_boot_ticket)&&
       ad->wr_iot_boot_frozen&&ad->wr_iot_boot_irq_state==1&&
       ad->wr_iot_boot_rx_state==2&&ad->wr_iot_boot_ctrl_state==2&&
       ad->wr_iot_boot_ring_stage==4&&!ad->wr_iot_boot_ring_busy&&
       !ad->wr_iot_boot_ring_failed&&!ad->wr_iot_mcu_sender_owner.messages&&
       wr_iot_mcu_sender_drained(&ad->wr_iot_mcu_sender_owner)&&
       OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
INT32 wr_iot_mcu_boot_irq_prepare(RTMP_ADAPTER *ad)
{
 ULONG flags=0,owner_flags=0;int ready,success=0;
 if(!ad||in_atomic()||irqs_disabled()||!wr_iot_boot_rx_restart_idle(ad)||
    wr_iot_mcu_boot_other_tx_idle(ad)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,&ad->wr_iot_boot_ticket)&&
       ad->wr_iot_boot_frozen&&!ad->wr_iot_boot_irq_state&&
       ad->wr_iot_boot_rx_state==2&&ad->wr_iot_boot_ctrl_state==2&&
       ad->wr_iot_boot_ring_stage==4&&!ad->wr_iot_boot_ring_busy&&
       !ad->wr_iot_boot_ring_failed&&OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags);
 if(ready)ad->wr_iot_boot_irq_state=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
 if(wr_iot_nettask_boot_irq_prepare(ad)==NDIS_STATUS_SUCCESS&&
    wr_iot_boot_rx_restart_idle(ad)&&wr_iot_mcu_boot_irq_prepare_owned(ad))success=1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 if(success&&!wr_iot_mcu_boot_context_matches(ad,&ad->wr_iot_boot_ticket))success=0;
 ad->wr_iot_boot_irq_state=success?2:3;
 if(!success)ad->wr_iot_boot_failed=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return success?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
