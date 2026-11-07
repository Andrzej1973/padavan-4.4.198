/* Main-open owner, after checked ROM entry. Completion is hardware preparation
 * only: no firmware epoch receipt, ledger reset, command thaw or data admission. */
static int wr_iot_mcu_boot_hw_publish(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket,unsigned int stage)
{
 ULONG flags=0,owner_flags=0;int ready;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial)||
    !wr_iot_mcu_boot_frozen_owned(ad))return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_context_matches(ad,ticket)&&ad->wr_iot_boot_hw_state==1&&
       stage==ad->wr_iot_boot_hw_stage+1&&
       !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_HALT_IN_PROGRESS);
 if(ready)ad->wr_iot_boot_hw_stage=stage;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
INT32 wr_iot_mcu_boot_hardware_prepare(RTMP_ADAPTER *ad,
 const struct wr_iot_mcu_boot_ticket *ticket)
{
 ULONG flags=0,owner_flags=0;int ready,success=0,have_initial=0;
 struct wr_iot_mcu_boot_ticket saved;WPDMA_GLO_CFG_STRUC initial;
 if(!ad||!ticket||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 saved=*ticket;ticket=&saved;
 if(!wr_iot_mcu_boot_peer_matches(ad,ticket->peer_serial))return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ready=wr_iot_mcu_boot_matches(ad,ticket)&&!ad->wr_iot_boot_hw_state&&
       !ad->wr_iot_boot_hw_stage&&ad->wr_iot_boot_mcu_only&&
       !ad->wr_iot_boot_ring_stage&&!ad->wr_iot_boot_ring_busy&&!ad->wr_iot_boot_ring_failed&&
       !ad->wr_iot_boot_ctrl_state&&!ad->wr_iot_boot_rx_state&&!ad->wr_iot_boot_irq_state&&
       !ad->wr_iot_boot_dma_state&&!ad->wr_iot_boot_dma_saved_valid&&!ad->wr_iot_boot_irq_unmask_state&&
       !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_HALT_IN_PROGRESS)&&
       OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags);
 if(ready)ad->wr_iot_boot_hw_state=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
 /* Retain a known disabled baseline even if ROM quiesce fails before the
  * dedicated DMA-start stage captures its own later configuration. */
 RTMP_IO_READ32(ad,MT_WPDMA_GLO_CFG,&initial.word);
 if(initial.word==~(UINT32)0)goto done;
 initial.field.EnableTxDMA=0;initial.field.EnableRxDMA=0;
 initial.field.TxDMABusy=0;initial.field.RxDMABusy=0;initial.field.EnTXWriteBackDDONE=0;
 have_initial=1;
 if(wr_iot_mcu_boot_ring_transaction(ad,ticket)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_hw_publish(ad,ticket,1))goto done;
 if(wr_iot_mcu_boot_controller_init(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_hw_publish(ad,ticket,2))goto done;
 if(wr_iot_mcu_boot_rx_restart(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_hw_publish(ad,ticket,3))goto done;
 if(wr_iot_mcu_boot_irq_prepare(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_hw_publish(ad,ticket,4))goto done;
 if(wr_iot_mcu_boot_dma_start(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_hw_publish(ad,ticket,5))goto done;
 if(wr_iot_mcu_boot_irq_unmask(ad)!=NDIS_STATUS_SUCCESS||
    !wr_iot_mcu_boot_hw_publish(ad,ticket,6))goto done;
 success=1;
done:
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 if(success&&(!wr_iot_mcu_boot_context_matches(ad,ticket)||
    RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_HALT_IN_PROGRESS)))success=0;
 if(success)ad->wr_iot_boot_hw_state=2;
 else{
  ad->wr_iot_boot_failed=1;
  /* Historical outer lease owns failure masking even before unmask began. */
  ad->wr_iot_boot_irq_unmask_state=1;
  if(!ad->wr_iot_boot_dma_saved_valid&&have_initial){
   ad->wr_iot_boot_dma_saved_off=initial.word;ad->wr_iot_boot_dma_saved_valid=1;
  }
  ad->wr_iot_boot_dma_state=1;
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(success)return NDIS_STATUS_SUCCESS;
 (void)wr_iot_nettask_boot_irq_abort(ad);
 (void)wr_iot_mcu_boot_dma_stop_hw(ad);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 ad->wr_iot_boot_irq_unmask_state=3;
 ad->wr_iot_boot_dma_state=ad->wr_iot_boot_dma_stop_verified?3:4;
 ad->wr_iot_boot_hw_state=3;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return NDIS_STATUS_FAILURE;
}
