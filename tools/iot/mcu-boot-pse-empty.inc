/* Known SDK PSE queue snapshot only. Never remove a frame, reset PSE,
 * clear sequence quarantine or treat this alone as a firmware epoch receipt. */
/* -1: invalid observation, 0: busy, 1: empty. */
static INT wr_iot_boot_pse_snapshot(RTMP_ADAPTER *ad)
{
 static const unsigned int queues[3]={3,4,14};
 UINT32 saved=0,value,query,selector_mask=GET_PID_MASK|GET_QID_MASK|GET_RVSE_MASK;
 unsigned int port,q;int saved_valid=0,ready=-1;
 NdisAcquireSpinLock(&ad->IndirectUpdateLock);
 if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))goto out;
 RTMP_IO_READ32(ad,GC,&value);
 if(value==~(UINT32)0 || !(value&PSE_INIT_DONE) ||
    (value&(PSE_ALL_RST|PSE_LOGICAL_RST)))goto out;
 RTMP_IO_READ32(ad,FC_SP0P1,&value);
 if(value==~(UINT32)0)goto out;
 if(GET_SRC_CNT_P0(value)||GET_SRC_CNT_P1(value)){ready=0;goto out;}
 RTMP_IO_READ32(ad,FC_SP2Q0Q1,&value);
 if(value==~(UINT32)0)goto out;
 if(GET_SRC_CNT_P2_RQ0(value)||GET_SRC_CNT_P2_RQ1(value)){ready=0;goto out;}
 RTMP_IO_READ32(ad,FC_SP2Q2,&value);
 if(value==~(UINT32)0)goto out;
 if(GET_SRC_CNT_P2_RQ2(value)){ready=0;goto out;}
 RTMP_IO_READ32(ad,C_GFF,&saved);
 if(saved==~(UINT32)0)goto out;
 saved_valid=1;
 for(port=0;port<3;port++)for(q=0;q<queues[port];q++){
  if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))goto out;
  query=(saved&~selector_mask)|SET_GET_PID(port)|SET_GET_QID(q);
  RTMP_IO_WRITE32(ad,C_GFF,query);
  RTMP_IO_READ32(ad,C_GFF,&value);
  if(value==~(UINT32)0 || (value&selector_mask)!=(query&selector_mask))goto out;
  if(GET_FIRST_FID(value)!=0xfffU){ready=0;goto out;}
 }
 ready=1;
out:
 if(saved_valid && !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST)){
  RTMP_IO_WRITE32(ad,C_GFF,saved);
  RTMP_IO_READ32(ad,C_GFF,&value);
  if(value==~(UINT32)0 || (value&selector_mask)!=(saved&selector_mask))ready=-1;
 }else if(saved_valid)ready=-1;
 NdisReleaseSpinLock(&ad->IndirectUpdateLock);
 return ready;
}
BOOLEAN wr_iot_mcu_boot_pse_empty(RTMP_ADAPTER *ad)
{
 UINT32 value;ULONG flags=0;unsigned int sample;int joined;
 if(!ad||in_atomic()||irqs_disabled()||!IS_MT7603(ad)||
    ad->chipCap.hif_type!=HIF_MT||!wr_iot_mcu_boot_frozen_owned(ad)||
    OS_TEST_BIT(MCU_INIT,&ad->MCUCtrl.flags))return FALSE;
 RTMP_INT_LOCK(&ad->wr_iot_nettask_lock,flags);
 joined=ad->wr_iot_nettask_joined&&ad->wr_iot_nettask_data_joined&&
        !ad->wr_iot_boot_mcu_only&&!ad->wr_iot_nettask_initializing&&
        !ad->wr_iot_nettask_data_joining&&
        wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_owner)&&
        wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_data_owner);
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,flags);
 if(!joined)return FALSE;
 for(sample=0;sample<2;sample++){
  if(!wr_iot_mcu_boot_frozen_owned(ad)||RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))return FALSE;
  RTMP_IO_READ32(ad,TOP_MISC2,&value);
  if(value==~(UINT32)0||(value&3U)!=1U)return FALSE;
  RTMP_IO_READ32(ad,ARB_SCR,&value);
  if(value==~(UINT32)0||(value&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
     (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))return FALSE;
  RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
  if(value||!wr_iot_mcu_dma_disabled_idle(ad)||wr_iot_boot_pse_snapshot(ad)!=1)return FALSE;
  if(!sample)RtmpusecDelay(1000);
 }
 return wr_iot_mcu_boot_frozen_owned(ad)?TRUE:FALSE;
}
