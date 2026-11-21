/* Bootstrap scheduler postcheck. Normal admission is a separate operation.
 * SDK quota/remap preflight and ownership receipt still require integration. */
INT32 wr_iot_mcu_boot_scheduler_check(RTMP_ADAPTER *ad)
{
 UINT32 value,expected,saved_remap;INT32 result;
 if(!ad||in_atomic()||irqs_disabled()||!IS_MT7603(ad)||ad->bPCIclkOff||
    !ad->wr_iot_boot_active||ad->wr_iot_boot_failed||
    ad->wr_iot_boot_frozen||ad->wr_iot_boot_hw_state!=2||
    ad->wr_iot_boot_hw_stage!=6||ad->MCUCtrl.Stage!=FW_RUN_TIME)
  return NDIS_STATUS_FAILURE;
#ifdef CONFIG_FPGA_MODE
 /* The SDK substitutes this field for the requested mode. */
 if(ad->fpga_ctl.dma_mode!=DMA_SCH_LMAC)return NDIS_STATUS_FAILURE;
#endif
 if(!wr_iot_mcu_boot_owned(ad))return NDIS_STATUS_FAILURE;
 if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|
    fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_SUSPEND))return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,TOP_MISC2,&value);
 if(value==~(UINT32)0||!(value&2U))return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,MCU_PCIE_REMAP_2,&saved_remap);
 if(saved_remap==~(UINT32)0)return NDIS_STATUS_FAILURE;
 result=AsicDMASchedulerInit(ad,DMA_SCH_LMAC);
 RTMP_IO_READ32(ad,MCU_PCIE_REMAP_2,&value);
 if(value!=saved_remap){
  RTMP_IO_WRITE32(ad,MCU_PCIE_REMAP_2,saved_remap);
  RTMP_IO_READ32(ad,MCU_PCIE_REMAP_2,&value);
  return NDIS_STATUS_FAILURE;
 }
 if(result!=TRUE)return NDIS_STATUS_FAILURE;
 expected=MTK_REV_GTE(ad,MT7603,MT7603E1)?0x40U:0U;
 RTMP_IO_READ32(ad,MT_SCH_REG_4,&value);
 if(value!=expected)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,TOP_MISC2,&value);
 if(value==~(UINT32)0||!(value&2U))return NDIS_STATUS_FAILURE;
 if(ad->bPCIclkOff||!ad->wr_iot_boot_active||ad->wr_iot_boot_failed||ad->wr_iot_boot_frozen||
    ad->wr_iot_boot_hw_state!=2||ad->wr_iot_boot_hw_stage!=6||
    ad->MCUCtrl.Stage!=FW_RUN_TIME)return NDIS_STATUS_FAILURE;
 if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RESET_IN_PROGRESS|
    fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_SUSPEND))return NDIS_STATUS_FAILURE;
 return wr_iot_mcu_boot_owned(ad)?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
