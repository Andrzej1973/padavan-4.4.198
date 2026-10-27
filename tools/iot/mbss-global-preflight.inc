/* Isolated source candidate. Call before the first MBSS beacon/netdev free.
 * This only gates removal; the PCI owner must still close and join children,
 * set wr_iot_pci_work_joined under this lock, and handle terminal failure. */
static inline INT wr_iot_mbss_global_preflight(RTMP_ADAPTER *pAd)
{
 ULONG flags;
 UINT bss, max_bss, published = 0;
 int ready = 0;
 if (!pAd) return NDIS_STATUS_FAILURE;
 max_bss = MAX_MBSSID_NUM(pAd);
 if (max_bss < FIRST_MBSSID || max_bss > WDEV_NUM_MAX)
  return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 if (!pAd->wr_iot_transition.retiring ||
     pAd->wr_iot_registration_inflight ||
     pAd->wr_iot_transition.active_tx)
  goto out;
 for (bss = FIRST_MBSSID; bss < max_bss; bss++)
  if (pAd->ApCfg.MBSSID[bss].wdev.if_dev)
   published++;
 ready = wr_iot_mbss_closes_joined(pAd->wr_iot_interface_refs,
  WDEV_NUM_MAX + 1, published, pAd->wr_iot_pci_work_joined);
out:
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 return ready ? NDIS_STATUS_SUCCESS : NDIS_STATUS_FAILURE;
}
