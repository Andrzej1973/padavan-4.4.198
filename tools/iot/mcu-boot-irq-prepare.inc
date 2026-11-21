/* Prepare software state for MCU RX1/control TX only. Hardware stays masked. */
INT wr_iot_nettask_boot_irq_prepare(RTMP_ADAPTER *ad)
{
 ULONG irq_flags=0,interrupt_flags=0,lane_flags=0;UINT32 value;
 const UINT32 mask=MT_INT_RX_CMD|MT_INT_CMD;int ready;
 if(!ad||in_atomic()||irqs_disabled()||!wr_iot_mcu_boot_irq_prepare_owned(ad))
  return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&ad->irq_lock,irq_flags);
 RTMP_INT_LOCK(&ad->LockInterrupt,interrupt_flags);
 RTMP_INT_LOCK(&ad->wr_iot_nettask_lock,lane_flags);
 ready=ad->wr_iot_boot_mcu_only&&!ad->wr_iot_nettask_initializing&&
       !ad->wr_iot_nettask_joined&&ad->wr_iot_nettask_data_joined&&
       !ad->wr_iot_nettask_data_joining&&!ad->wr_iot_nettask_owner.blocked&&
       !ad->wr_iot_nettask_owner.poisoned&&!ad->wr_iot_nettask_owner.inflight&&
       wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_data_owner);
 if(!ready)goto fail;
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);if(value)goto fail;
 RTMP_IO_READ32(ad,MT_WPDMA_GLO_CFG,&value);
 if(value==~(UINT32)0||(value&(TX_DMA_EN|RX_DMA_EN|TX_DMA_BUSY|RX_DMA_BUSY)))goto fail;
 RTMP_IO_READ32(ad,MT_INT_SOURCE_CSR,&value);if(value==~(UINT32)0)goto fail;
 ad->wr_iot_boot_irq_saved_enable=ad->int_enable_reg;
 ad->wr_iot_boot_irq_saved_disable=ad->int_disable_mask;
 ad->wr_iot_boot_irq_saved_pending=ad->int_pending;
 ad->int_enable_reg=mask;ad->int_disable_mask=mask;ad->int_pending&=~mask;
 RTMP_IO_WRITE32(ad,MT_INT_MASK_CSR,0);
 RTMP_CLEAR_FLAG(ad,fRTMP_ADAPTER_INTERRUPT_ACTIVE);
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);if(value)goto fail;
 /* W1C only the two bootstrap sources; preserve unrelated pending sources. */
 RTMP_IO_WRITE32(ad,MT_INT_SOURCE_CSR,mask);
 RTMP_IO_READ32(ad,MT_INT_SOURCE_CSR,&value);
 if(value==~(UINT32)0||(value&mask))goto fail;
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,lane_flags);
 RTMP_INT_UNLOCK(&ad->LockInterrupt,interrupt_flags);
 RTMP_INT_UNLOCK(&ad->irq_lock,irq_flags);
 return wr_iot_mcu_boot_irq_prepare_owned(ad)?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
fail:
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,lane_flags);
 RTMP_INT_UNLOCK(&ad->LockInterrupt,interrupt_flags);
 RTMP_INT_UNLOCK(&ad->irq_lock,irq_flags);
 return NDIS_STATUS_FAILURE;
}
