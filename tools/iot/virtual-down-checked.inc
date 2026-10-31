/* Candidate: sole ticket owner pins resources; all count writers need same owner. */
INT wr_iot_virtual_down_checked(RTMP_ADAPTER *pAd,
 const struct wr_iot_radio_ticket *ticket)
{
 ULONG flags;
 unsigned int stage;
 if (!pAd || !ticket) return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 if ((ticket->operation != WR_RADIO_CLOSE && ticket->operation != WR_RADIO_BSS_CLOSE &&
      ticket->operation != WR_RADIO_AUX_CLOSE) ||
     pAd->wr_iot_transition.busy != ticket->operation ||
     pAd->wr_iot_transition.serial != ticket->serial) {
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }
 stage=pAd->wr_iot_transition.virtual_down_stage;
 if (stage == 2U) {
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_SUCCESS;
 }
 if (stage > 1U) {
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }
 if (ticket->operation == WR_RADIO_BSS_CLOSE || ticket->operation == WR_RADIO_AUX_CLOSE) {
  if (stage || VIRTUAL_IF_NUM(pAd) <= 1U) {
   RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
   return NDIS_STATUS_FAILURE;
  }
  VIRTUAL_IF_DEC(pAd);
  pAd->wr_iot_transition.virtual_down_stage=2U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_SUCCESS;
 }
 if ((stage == 0U && VIRTUAL_IF_NUM(pAd) != 1U) ||
     (stage == 1U && VIRTUAL_IF_NUM(pAd) != 0U)) {
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }
 if (!stage) {
  VIRTUAL_IF_DEC(pAd);
  pAd->wr_iot_transition.virtual_down_stage=1U;
 }
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 if (wr_iot_rt28xx_close_checked(pAd->net_dev,ticket) != 0)
  return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 pAd->wr_iot_transition.virtual_down_stage=2U;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return NDIS_STATUS_SUCCESS;
}
