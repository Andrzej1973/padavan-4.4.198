/* Core side of kernel-owned peer-open ioctl. No adapter layout crosses NETIF.
 * Success here reserves bootstrap only; it never publishes normal readiness. */
static int wr_iot_boot_open_peer_valid(RTMP_ADAPTER *ad,unsigned long serial)
{
 struct wr_iot_peer_open_ticket ticket;int ready;
 ticket.device=ad->net_dev;ticket.serial=serial;
 NdisAcquireSpinLock(&ad->MacTabLock);
 ready=wr_iot_peer_open_matches(&ad->wr_iot_peer_open_owner,
       &ad->wr_iot_peer_table_owner,&ticket) &&
       ad->wr_iot_peer_open_owner.phase==WR_PEER_OPEN_CONFIG &&
       wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor);
 NdisReleaseSpinLock(&ad->MacTabLock);
 return ready;
}
INT wr_iot_boot_open_prepare(RTMP_ADAPTER *ad,unsigned long peer_serial)
{
#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)
 ULONG flags=0;int cold,claimed;
 #ifndef LOAD_FW_ONE_TIME
 struct wr_iot_mcu_boot_ticket ticket;
 #endif
#endif
 if(!ad||!peer_serial||!wr_iot_boot_open_peer_valid(ad,peer_serial))return NDIS_STATUS_FAILURE;
#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)
 if(!IS_MT7603(ad)||ad->chipCap.hif_type!=HIF_MT)return NDIS_STATUS_SUCCESS;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 claimed=ad->wr_iot_mcu_sender_owner.release_claimed;
 cold=!claimed && !ad->wr_iot_boot_active && !ad->wr_iot_boot_failed &&
      !ad->wr_iot_mcu_sender_owner.closed && !ad->wr_iot_mcu_sender_owner.poisoned &&
      !ad->wr_iot_mcu_sender_owner.uncertain && !ad->wr_iot_mcu_sender_owner.messages &&
      !ad->wr_iot_mcu_sender_owner.inflight && !ad->wr_iot_mcu_sender_owner.radio_active &&
      !ad->wr_iot_mcu_sender_owner.off_active;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 if(cold)return NDIS_STATUS_SUCCESS;
 if(!claimed)return NDIS_STATUS_FAILURE;
#ifdef LOAD_FW_ONE_TIME
 return NDIS_STATUS_FAILURE;
#else
 return wr_iot_mcu_boot_reserve(ad,peer_serial,&ticket);
#endif
#else
 return NDIS_STATUS_SUCCESS;
#endif
}
/* Narrow IRQ-release gate after failed init. It does not allow adapter free,
 * clear uncertain sequence ownership, or attempt a second destructive unwind. */
INT wr_iot_boot_open_irq_ready(RTMP_ADAPTER *ad,unsigned long peer_serial)
{
#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)
 ULONG flags=0;int ready;
#endif
 if(!ad||!peer_serial)return NDIS_STATUS_FAILURE;
#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)
 if(!ad->wr_iot_boot_active)return NDIS_STATUS_SUCCESS;
 if(!wr_iot_boot_open_peer_valid(ad,peer_serial))return NDIS_STATUS_FAILURE;
 if(ad->wr_iot_boot_ticket.peer_serial!=peer_serial ||
    OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags))return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&ad->wr_iot_nettask_lock,flags);
 ready=!ad->wr_iot_boot_mcu_only && !ad->wr_iot_nettask_initializing &&
       ad->wr_iot_nettask_joined && ad->wr_iot_nettask_data_joined &&
       !ad->wr_iot_nettask_data_joining &&
       wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_owner) &&
       wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_data_owner);
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&flags);
 ready=ready && !ad->wr_iot_mcu_sender_owner.messages &&
       !ad->wr_iot_mcu_sender_owner.inflight && !ad->wr_iot_mcu_sender_owner.radio_active &&
       !ad->wr_iot_mcu_sender_owner.off_active;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&flags);
 if(!ready || !wr_iot_mcu_dma_disabled_idle(ad))return NDIS_STATUS_FAILURE;
#endif
 return NDIS_STATUS_SUCCESS;
}
