/* Release only RX1/TX5 after checked DMA start. Constructors stay frozen. */
INT wr_iot_nettask_boot_irq_unmask(RTMP_ADAPTER *ad)
{
 ULONG irq_flags=0,interrupt_flags=0,lane_flags=0;UINT32 value;
 const UINT32 mask=MT_INT_RX_CMD|MT_INT_CMD;int ready;
 if(!ad||in_atomic()||irqs_disabled()||!wr_iot_mcu_boot_irq_unmask_owned(ad))return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&ad->irq_lock,irq_flags);
 RTMP_INT_LOCK(&ad->LockInterrupt,interrupt_flags);
 RTMP_INT_LOCK(&ad->wr_iot_nettask_lock,lane_flags);
 ready=ad->wr_iot_boot_mcu_only&&!ad->wr_iot_nettask_initializing&&
       !ad->wr_iot_nettask_joined&&ad->wr_iot_nettask_data_joined&&
       !ad->wr_iot_nettask_data_joining&&!ad->wr_iot_nettask_owner.blocked&&
       !ad->wr_iot_nettask_owner.poisoned&&!ad->wr_iot_nettask_owner.inflight&&
       wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_data_owner)&&
       ad->int_enable_reg==mask&&ad->int_disable_mask==mask&&!(ad->int_pending&mask);
 if(!ready||RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|
    fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_START_UP))goto fail;
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);if(value)goto fail;
 RTMP_IO_READ32(ad,MT_WPDMA_GLO_CFG,&value);
 if(value==~(UINT32)0||(value&(TX_DMA_EN|RX_DMA_EN))!=(TX_DMA_EN|RX_DMA_EN))goto fail;
 RTMP_IO_READ32(ad,ARB_SCR,&value);
 if(value==~(UINT32)0||(value&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
    (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))goto fail;
 ad->wr_iot_boot_irq_startup_owned=1;
 RTMP_SET_FLAG(ad,fRTMP_ADAPTER_START_UP|fRTMP_ADAPTER_INTERRUPT_ACTIVE);
 ad->int_disable_mask=0;
 wmb();
 RTMP_IO_WRITE32(ad,MT_INT_MASK_CSR,mask);
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);if(value!=mask)goto fail;
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,lane_flags);
 RTMP_INT_UNLOCK(&ad->LockInterrupt,interrupt_flags);
 RTMP_INT_UNLOCK(&ad->irq_lock,irq_flags);
 return NDIS_STATUS_SUCCESS;
fail:
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,lane_flags);
 RTMP_INT_UNLOCK(&ad->LockInterrupt,interrupt_flags);
 RTMP_INT_UNLOCK(&ad->irq_lock,irq_flags);
 return NDIS_STATUS_FAILURE;
}
/* Historical exclusive lease: usable even when peer/epoch validation failed.
 * Block tasklet rearm before masking. Do not free any tasklet/ring/controller. */
INT wr_iot_nettask_boot_irq_abort(RTMP_ADAPTER *ad)
{
 ULONG irq_flags=0,interrupt_flags=0,lane_flags=0;UINT32 value;
 if(!ad||ad->wr_iot_boot_irq_unmask_state!=1)return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&ad->irq_lock,irq_flags);
 RTMP_INT_LOCK(&ad->LockInterrupt,interrupt_flags);
 RTMP_INT_LOCK(&ad->wr_iot_nettask_lock,lane_flags);
 wr_iot_tasklet_schedule_block(&ad->wr_iot_nettask_owner);
 ad->int_disable_mask|=MT_INT_RX_CMD|MT_INT_CMD;
 RTMP_IO_WRITE32(ad,MT_INT_MASK_CSR,0);
 RTMP_CLEAR_FLAG(ad,fRTMP_ADAPTER_INTERRUPT_ACTIVE);
 if(ad->wr_iot_boot_irq_startup_owned){
  RTMP_CLEAR_FLAG(ad,fRTMP_ADAPTER_START_UP);ad->wr_iot_boot_irq_startup_owned=0;
 }
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,lane_flags);
 RTMP_INT_UNLOCK(&ad->LockInterrupt,interrupt_flags);
 RTMP_INT_UNLOCK(&ad->irq_lock,irq_flags);
 return value?NDIS_STATUS_FAILURE:NDIS_STATUS_SUCCESS;
}
