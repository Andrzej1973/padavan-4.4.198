/* Checked MT7603 halt path. The CLOSE ticket pins this adapter and excludes
 * concurrent radio writers. An uncertain MCU result is terminal for this
 * attempt: replaying a command whose completion is unknown is not safe. */
BOOLEAN wr_iot_mt_radio_off_checked(RTMP_ADAPTER *pAd,
 const struct wr_iot_radio_ticket *ticket)
{
 WPDMA_GLO_CFG_STRUC cfg;
 ULONG flags;
 UINT32 arb;
 unsigned int stage;
 INT32 bss;
 if (!pAd || !ticket || !pAd->net_dev || !IS_MT7603(pAd) ||
     pAd->chipCap.hif_type != HIF_MT ||
     RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST) ||
     pAd->iwpriv_command)
  return FALSE;
#ifdef LOAD_FW_ONE_TIME
 /* This build uses an AGG_TEMP write without an MCU result. */
 return FALSE;
#endif
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 if (ticket->operation != WR_RADIO_CLOSE ||
     pAd->wr_iot_transition.busy != WR_RADIO_CLOSE ||
     pAd->wr_iot_transition.serial != ticket->serial) {
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  return FALSE;
 }
 stage = pAd->wr_iot_transition.mt_radio_off_stage;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 if (stage == 4U) return TRUE;
 if (stage > 4U) return FALSE;
 if (stage == 0U) {
  RTMP_OS_NETDEV_STOP_QUEUE(pAd->net_dev);
#ifdef CONFIG_AP_SUPPORT
  IF_DEV_CONFIG_OPMODE_ON_AP(pAd) {
   for (bss = FIRST_MBSSID; bss < MAX_MBSSID_NUM(pAd); bss++)
    if (pAd->ApCfg.MBSSID[bss].wdev.if_dev)
     RTMP_OS_NETDEV_STOP_QUEUE(pAd->ApCfg.MBSSID[bss].wdev.if_dev);
  }
#else
  (void)bss;
#endif
  RTMP_SET_FLAG(pAd, fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET);
  if (!AsicSetMacTxRx(pAd, ASIC_MAC_RX, FALSE)) return FALSE;
  RTMP_IO_READ32(pAd, ARB_SCR, &arb);
  if (arb == 0xffffffffU || !(arb & MT_ARB_SCR_RXDIS)) return FALSE;
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  pAd->wr_iot_transition.mt_radio_off_stage = 1U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  stage = 1U;
 }
 if (stage == 1U) {
  if (!wr_iot_mt_poll_txrx_empty(pAd)) return FALSE;
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  pAd->wr_iot_transition.mt_radio_off_stage = 2U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  stage = 2U;
 }
 if (stage == 2U) {
  if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST)) return FALSE;
  if (CmdRadioOnOffCtrl(pAd, WIFI_RADIO_OFF) != NDIS_STATUS_SUCCESS) {
   RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
   pAd->wr_iot_transition.mt_radio_off_stage = 5U;
   RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
   return FALSE;
  }
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  pAd->wr_iot_transition.mt_radio_off_stage = 3U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  stage = 3U;
 }
 if (stage == 3U) {
  if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST)) return FALSE;
  /* Keep MAC TX enabled until the MCU radio-off command has completed.
   * AsicSetMacTxRx() reports success without checking the register write. */
  if (!AsicSetMacTxRx(pAd, ASIC_MAC_TXRX, FALSE)) return FALSE;
  RTMP_IO_READ32(pAd, ARB_SCR, &arb);
  if (arb == 0xffffffffU ||
      (arb & (MT_ARB_SCR_TXDIS | MT_ARB_SCR_RXDIS)) !=
       (MT_ARB_SCR_TXDIS | MT_ARB_SCR_RXDIS))
   return FALSE;
  if (!AsicSetWPDMA(pAd, PDMA_TX_RX, FALSE)) return FALSE;
  RTMP_IO_READ32(pAd, MT_WPDMA_GLO_CFG, &cfg.word);
  if (cfg.word == 0xffffffffU || cfg.field.EnableTxDMA ||
      cfg.field.EnableRxDMA || (cfg.word & (TX_DMA_BUSY | RX_DMA_BUSY)))
   return FALSE;
  RTMP_SET_FLAG(pAd, fRTMP_ADAPTER_RADIO_OFF);
  if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_INTERRUPT_ACTIVE))
   RTMP_ASIC_INTERRUPT_DISABLE(pAd);
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  pAd->wr_iot_transition.mt_radio_off_stage = 4U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 }
 /* MCU command accepted and PDMA disabled/idle. Device runtime observation
  * and callback retirement remain separate release gates. */
 return TRUE;
}
