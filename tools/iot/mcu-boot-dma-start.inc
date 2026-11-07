/* Checked shared DMA only. IRQ stays masked, MAC TX/RX and constructors closed. */
INT32 wr_iot_mcu_boot_dma_start_hw(RTMP_ADAPTER *ad)
{
 WPDMA_GLO_CFG_STRUC cfg;UINT32 value,expected;
 if(!ad||in_atomic()||irqs_disabled()||!wr_iot_mcu_boot_dma_owned(ad)||
    ad->chipCap.WPDMABurstSIZE>3)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);if(value)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,ARB_SCR,&value);
 if(value==~(UINT32)0||(value&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
    (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,MT_WPDMA_GLO_CFG,&cfg.word);
 if(cfg.word==~(UINT32)0||(cfg.word&(TX_DMA_EN|RX_DMA_EN|TX_DMA_BUSY|RX_DMA_BUSY)))return NDIS_STATUS_FAILURE;
 ad->wr_iot_boot_dma_saved_off=cfg.word;ad->wr_iot_boot_dma_saved_valid=1;
 cfg.field.EnableTxDMA=1;cfg.field.EnableRxDMA=1;
 cfg.field.EnTXWriteBackDDONE=1;cfg.field.WPDMABurstSIZE=ad->chipCap.WPDMABurstSIZE;
 expected=cfg.word;
 RTMP_IO_WRITE32(ad,MT_WPDMA_GLO_CFG,expected);
 RTMP_IO_READ32(ad,MT_WPDMA_GLO_CFG,&value);
 if(value==~(UINT32)0||(value&~(TX_DMA_BUSY|RX_DMA_BUSY))!=expected)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);if(value)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,ARB_SCR,&value);
 if(value==~(UINT32)0||(value&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
    (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))return NDIS_STATUS_FAILURE;
 return wr_iot_mcu_boot_dma_owned(ad)?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
/* Historical exclusive lease may stop after context loss; no resources freed. */
INT32 wr_iot_mcu_boot_dma_stop_hw(RTMP_ADAPTER *ad)
{
 UINT32 value;
 if(!ad||ad->wr_iot_boot_dma_state!=1||!ad->wr_iot_boot_dma_saved_valid)
  return NDIS_STATUS_FAILURE;
 RTMP_ASIC_INTERRUPT_DISABLE(ad);
 RTMP_IO_WRITE32(ad,MT_WPDMA_GLO_CFG,ad->wr_iot_boot_dma_saved_off);
 ad->wr_iot_boot_dma_stop_verified=wr_iot_mcu_dma_disabled_idle(ad)?1:0;
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 if(value)ad->wr_iot_boot_dma_stop_verified=0;
 return ad->wr_iot_boot_dma_stop_verified?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
