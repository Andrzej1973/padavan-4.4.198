/* Recreate software MCU queues/BH only after the owned ring transaction.
 * No IRQ/DMA enable, RX tasklet restart, ledger reset or command admission. */
INT32 wr_iot_mcu_boot_controller_init(RTMP_ADAPTER *ad)
{
 ULONG flags=0,owner_flags=0;int ready,success=0;
 if(!ad||in_atomic()||irqs_disabled()||ad->chipOps.MCUCtrlInit!=AndesCtrlInit||
    !wr_iot_mcu_boot_pse_empty(ad))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,&ad->wr_iot_boot_ticket)&&
       ad->wr_iot_boot_frozen&&ad->wr_iot_boot_ring_stage==4&&
       !ad->wr_iot_boot_ring_busy&&!ad->wr_iot_boot_ring_failed&&
       !ad->wr_iot_boot_ctrl_state&&!OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags);
 if(ready)ad->wr_iot_boot_ctrl_state=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
 if(wr_iot_boot_ctrl_pci_init(ad)!=NDIS_STATUS_SUCCESS)goto done;
 if(!wr_iot_mcu_boot_frozen_owned(ad))goto done;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 success=wr_iot_mcu_boot_context_matches(ad,&ad->wr_iot_boot_ticket)&&
         ad->wr_iot_boot_frozen&&ad->wr_iot_boot_ring_stage==4&&
         ad->wr_iot_boot_ctrl_state==1&&OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags);
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
done:
 /* Only this lease could have created the controller; no hardware was enabled. */
 if(!success&&OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags))AndesCtrlExit(ad);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ad->wr_iot_boot_ctrl_state=success?2:3;
 if(!success)ad->wr_iot_boot_failed=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return success?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
