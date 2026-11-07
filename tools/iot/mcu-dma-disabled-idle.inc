/* Candidate readback only, after firmware stop has disabled DMA. Caller owns
 * lifecycle and adapter pin. No bus-access receipt or hardware epoch implied. */
static BOOLEAN wr_iot_mcu_dma_disabled_idle(RTMP_ADAPTER *ad)
{
 UINT32 value;unsigned int attempt,clean=0;
 for(attempt=0;attempt<200;attempt++){
  if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))return FALSE;
  RTMP_IO_READ32(ad,MT_WPDMA_GLO_CFG,&value);
  if(value==~(UINT32)0 || RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))return FALSE;
  if(value&(TX_DMA_EN|RX_DMA_EN|TX_DMA_BUSY|RX_DMA_BUSY))clean=0;
  else if(++clean==2)return TRUE;
  RtmpusecDelay(1000);
 }
 return FALSE;
}
