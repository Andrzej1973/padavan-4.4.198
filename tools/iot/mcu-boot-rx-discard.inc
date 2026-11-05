/* Linux coherent RX descriptors, as allocated by RtmpAllocDescBuf. Caller is
 * the sole bootstrap consumer: IRQ masked/synchronized, both callback lanes
 * joined, boot constructors frozen. Payload mappings remain device-owned;
 * no payload read, parser, allocation, packet release or AP callback occurs.
 * One batch is bounded. Empty is a snapshot, not a hardware epoch receipt. */
INT wr_iot_mcu_boot_rx_discard_batch(RTMP_ADAPTER *ad,unsigned int *empty)
{
 UINT32 value,hw,control;ULONG flags=0;
 unsigned int ring,index,count,all_empty=1;int joined;
 RTMP_RX_RING *rx;RTMP_DMACB *cell;
 union {RXD_STRUC descriptor;UINT32 word[RXD_SIZE/sizeof(UINT32)];} local;
 if(empty)*empty=0;
 if(!ad||!empty||in_atomic()||irqs_disabled()||!IS_MT7603(ad)||
    ad->chipCap.hif_type!=HIF_MT||NUM_OF_RX_RING!=2||RX_RING_SIZE<2||
    RXD_SIZE<2*sizeof(UINT32)||sizeof(RXD_STRUC)>RXD_SIZE||
    RX_BUFFER_AGGRESIZE>0x3fffU||
    !wr_iot_mcu_boot_frozen_owned(ad))return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&ad->wr_iot_nettask_lock,flags);
 joined=ad->wr_iot_nettask_joined&&ad->wr_iot_nettask_data_joined&&
        !ad->wr_iot_boot_mcu_only&&!ad->wr_iot_nettask_initializing&&
        !ad->wr_iot_nettask_data_joining&&
        wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_owner)&&
        wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_data_owner);
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,flags);
 if(!joined || RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);
 if(value)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,TOP_MISC2,&value);
 if(value==~(UINT32)0||(value&3U)!=1U)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,ARB_SCR,&value);
 if(value==~(UINT32)0||(value&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
    (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))return NDIS_STATUS_FAILURE;
 /* Validate both inventories before recycling any descriptor. */
 for(ring=0;ring<2;ring++){
  rx=&ad->RxRing[ring];
  if(!ad->RxDescRing[ring].AllocVa ||
     ad->RxDescRing[ring].AllocSize<RX_RING_SIZE*RXD_SIZE ||
     rx->RxSwReadIdx>=RX_RING_SIZE||rx->RxCpuIdx>=RX_RING_SIZE||
     rx->hw_cidx_addr!=MT_RX_RING_CIDX+MT_RINGREG_DIFF*ring||
     rx->hw_didx_addr!=MT_RX_RING_DIDX+MT_RINGREG_DIFF*ring)return NDIS_STATUS_FAILURE;
  for(index=0;index<RX_RING_SIZE;index++){
   cell=&rx->Cell[index];
   if(cell->AllocVa!=(UCHAR *)ad->RxDescRing[ring].AllocVa+index*RXD_SIZE ||
      ((ULONG)cell->AllocVa&(sizeof(UINT32)-1)) || cell->AllocSize!=RXD_SIZE ||
      !cell->pNdisPacket || !cell->DmaBuf.AllocVa ||
      cell->DmaBuf.AllocSize!=RX_BUFFER_AGGRESIZE)return NDIS_STATUS_FAILURE;
  }
 }
 for(ring=0;ring<2;ring++){
  if(!wr_iot_mcu_boot_frozen_owned(ad))return NDIS_STATUS_FAILURE;
  rx=&ad->RxRing[ring];
  RTMP_SEM_LOCK(&ad->RxRingLock[ring]);
  RTMP_IO_READ32(ad,rx->hw_cidx_addr,&value);
  if(value!=rx->RxCpuIdx)goto ring_fail;
  for(count=0;count<RX_RING_SIZE;count++){
   if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_NIC_NOT_EXIST))goto ring_fail;
   RTMP_IO_READ32(ad,rx->hw_didx_addr,&hw);
   if(hw>=RX_RING_SIZE)goto ring_fail;
   rx->RxDmaIdx=hw;index=rx->RxSwReadIdx;cell=&rx->Cell[index];
   if(le2cpu32(((volatile UINT32 *)cell->AllocVa)[0])!=
      RTMP_GetPhysicalAddressLow(cell->DmaBuf.AllocPa))goto ring_fail;
   control=((volatile UINT32 *)cell->AllocVa)[1];
   local.word[1]=le2cpu32(control);
   if(!local.descriptor.DDONE){if(hw!=index)all_empty=0;break;}
   rmb();
   local.descriptor.SDL0=cell->DmaBuf.AllocSize;
   local.descriptor.SDL1=0;local.descriptor.LS0=0;local.descriptor.LS1=0;
   local.descriptor.DDONE=0;
   wmb();
   /* Publish only the ownership/control word, preserving DMA addresses. */
   ((volatile UINT32 *)cell->AllocVa)[1]=cpu2le32(local.word[1]);
   wmb();
   rx->RxCpuIdx=index;rx->RxSwReadIdx=(index+1)%RX_RING_SIZE;
   RTMP_IO_WRITE32(ad,rx->hw_cidx_addr,rx->RxCpuIdx);
   RTMP_IO_READ32(ad,rx->hw_cidx_addr,&value);
   if(value!=rx->RxCpuIdx)goto ring_fail;
  }
  if(count==RX_RING_SIZE)all_empty=0;
  RTMP_SEM_UNLOCK(&ad->RxRingLock[ring]);
 }
 if(!wr_iot_mcu_boot_frozen_owned(ad))return NDIS_STATUS_FAILURE;
 *empty=all_empty;return NDIS_STATUS_SUCCESS;
ring_fail:
 RTMP_SEM_UNLOCK(&ad->RxRingLock[ring]);
 return NDIS_STATUS_FAILURE;
}
