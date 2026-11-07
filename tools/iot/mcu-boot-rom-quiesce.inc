/* Method1 initialization owner, after a successful NETIF IRQ request. This
 * joins software consumers and stops DMA in ROM; it does NOT establish a
 * fresh RX/control-ring epoch, clear sequence quarantine or reopen admission. */
INT32 wr_iot_mcu_boot_rom_quiesce(RTMP_ADAPTER *ad)
{
 POS_COOKIE cookie;
 struct MCU_CTRL *ctl;
 UINT32 value;
 if(!ad||in_atomic()||irqs_disabled()||!IS_MT7603(ad)||
    ad->chipCap.hif_type!=HIF_MT||ad->chipOps.MCUCtrlExit!=AndesCtrlExit||
    !wr_iot_mcu_boot_owned(ad))return NDIS_STATUS_FAILURE;
 cookie=(POS_COOKIE)ad->OS_Cookie;ctl=&ad->MCUCtrl;
 if(!cookie||!cookie->pci_dev||!ad->wr_iot_boot_mcu_only||
    !OS_TEST_BIT(MCU_INIT,&ctl->flags)||
    RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,TOP_MISC2,&value);
 if(value==~(UINT32)0||(value&3U)!=1U)return NDIS_STATUS_FAILURE;
 if(wr_iot_mcu_boot_freeze(ad)!=NDIS_STATUS_SUCCESS ||
    !wr_iot_mcu_boot_frozen_owned(ad))return NDIS_STATUS_FAILURE;
 AndesMTPciFwExit(ad);
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 if(value!=0 || !wr_iot_mcu_dma_disabled_idle(ad))return NDIS_STATUS_FAILURE;
 /* IRQ remains registered. No lock is held across synchronization/joins. */
 synchronize_irq(cookie->pci_dev->irq);
 if(RtmpNetTaskExit(ad)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;
 if(!wr_iot_mcu_boot_frozen_owned(ad))return NDIS_STATUS_FAILURE;
 if(AndesQueueLen(ctl,&ctl->txq)||AndesQueueLen(ctl,&ctl->ackq)||
    AndesQueueLen(ctl,&ctl->rxq)||AndesQueueLen(ctl,&ctl->kickq)||
    AndesQueueLen(ctl,&ctl->tx_doneq)||AndesQueueLen(ctl,&ctl->rx_doneq))return NDIS_STATUS_FAILURE;
 MCU_CTRL_EXIT(ad);
 if(OS_TEST_BIT(MCU_INIT,&ctl->flags) || !wr_iot_mcu_boot_frozen_owned(ad) ||
    RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,TOP_MISC2,&value);
 if(value==~(UINT32)0||(value&3U)!=1U)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 if(value || !wr_iot_mcu_dma_disabled_idle(ad))return NDIS_STATUS_FAILURE;
 return NDIS_STATUS_SUCCESS;
}
