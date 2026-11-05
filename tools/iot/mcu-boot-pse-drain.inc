/* Sole frozen bootstrap owner, with MAC producers stopped and callbacks joined.
 * Empty observations do not rearm normal admission or retire sequence IDs. */
INT32 wr_iot_mcu_boot_pse_drain(RTMP_ADAPTER *ad,unsigned int live_rx)
{
 unsigned int attempt,empty,consecutive=0;UINT32 cfg;INT observed;
 if(!ad||live_rx>1||in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 for(attempt=0;attempt<200;attempt++){
  if(!wr_iot_mcu_boot_frozen_owned(ad)||RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))return NDIS_STATUS_FAILURE;
  RTMP_IO_READ32(ad,MT_WPDMA_GLO_CFG,&cfg);
  if(cfg==~(UINT32)0)return NDIS_STATUS_FAILURE;
  if(live_rx){if(!(cfg&RX_DMA_EN))return NDIS_STATUS_FAILURE;}
  else if(cfg&(TX_DMA_EN|RX_DMA_EN|TX_DMA_BUSY|RX_DMA_BUSY))return NDIS_STATUS_FAILURE;
  /* This primitive checks ROM, IRQ mask, MAC stop and joined lanes itself. */
  if(wr_iot_mcu_boot_rx_discard_batch(ad,&empty)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;
  observed=wr_iot_boot_pse_snapshot(ad);
  if(observed<0)return NDIS_STATUS_FAILURE;
  if(!live_rx&&!observed)return NDIS_STATUS_FAILURE;
  if(empty&&observed==1){if(++consecutive==2)return wr_iot_mcu_boot_frozen_owned(ad)?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;}
  else consecutive=0;
  if(attempt+1<200)RtmpusecDelay(1000);
 }
 return NDIS_STATUS_FAILURE;
}
