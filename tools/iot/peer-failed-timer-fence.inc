/* Insertion holds MacTabLock. Match the exact initialization branches;
 * this fences future scheduling, never claims an executing callback joined. */
 wr_iot_timer_fence(&pEntry->EnqueueStartForPSKTimer);
#ifdef CONFIG_AP_SUPPORT
 if (IS_ENTRY_CLIENT(pEntry)) {
  wr_iot_timer_fence(&pEntry->RetryTimer);
#ifdef DOT11W_PMF_SUPPORT
  wr_iot_timer_fence(&pEntry->SAQueryTimer);
  wr_iot_timer_fence(&pEntry->SAQueryConfirmTimer);
#endif
#if defined(MT_MAC) && defined(WSC_INCLUDED)
  wr_iot_timer_fence(&pEntry->EapReqIdRetryTimer);
#endif
 }
#ifdef APCLI_SUPPORT
 if (IS_ENTRY_APCLI(pEntry)) {
  wr_iot_timer_fence(&pEntry->RetryTimer);
#if defined(APCLI_DOT11W_PMF_SUPPORT) && defined(DOT11W_PMF_SUPPORT)
  wr_iot_timer_fence(&pEntry->SAQueryTimer);
  wr_iot_timer_fence(&pEntry->SAQueryConfirmTimer);
#endif
 }
#endif
#endif
