/* Program only CTRL(5), RX0 and RX1 with DMA/IRQ off. This is not firmware
 * epoch commit and never enables DMA, tasklets or ordinary command admission. */
INT wr_iot_mcu_boot_ring_rearm(RTMP_ADAPTER *ad)
{
 struct wr_ring {UINT32 base,count,cpu,dma,pa,size,cidx;} rings[3];
 WPDMA_RST_IDX_STRUC reset;UINT32 value;unsigned int i,j;
 RTMP_DMACB *cell;TXD_STRUC *tx;RXD_STRUC *rx;
 if(!ad||in_atomic()||irqs_disabled()||NUM_OF_RX_RING!=2||
    TXD_SIZE<sizeof(TXD_STRUC)||RXD_SIZE<sizeof(RXD_STRUC)||
    !wr_iot_mcu_boot_pse_empty(ad))return NDIS_STATUS_FAILURE;
 NdisZeroMemory(&reset,sizeof(reset));
 reset.field.RST_DTX_IDX5=1;reset.field.RST_DRX_IDX0=1;reset.field.RST_DRX_IDX1=1;
 for(i=0;i<3;i++){
  RTMP_DMABUF *buf=i?&ad->RxDescRing[i-1]:&ad->CtrlDescRing;
  unsigned int stride=i?RXD_SIZE:TXD_SIZE,size=i?RX_RING_SIZE:MGMT_RING_SIZE;
  if(!buf->AllocVa||((ULONG)buf->AllocVa&(sizeof(UINT32)-1))||buf->AllocSize<size*stride||
     RTMP_GetPhysicalAddressHigh(buf->AllocPa)||
     (RTMP_GetPhysicalAddressLow(buf->AllocPa)&15U))return NDIS_STATUS_FAILURE;
  for(j=0;j<size;j++){
   cell=i?&ad->RxRing[i-1].Cell[j]:&ad->CtrlRing.Cell[j];
   if(cell->AllocVa!=(UCHAR *)buf->AllocVa+j*stride||cell->AllocSize!=stride||
      RTMP_GetPhysicalAddressHigh(cell->AllocPa)||
      RTMP_GetPhysicalAddressLow(cell->AllocPa)!=RTMP_GetPhysicalAddressLow(buf->AllocPa)+j*stride)
    return NDIS_STATUS_FAILURE;
   if(!i){
    tx=(TXD_STRUC *)cell->AllocVa;
    if(cell->pNdisPacket||cell->pNextNdisPacket||!tx->DMADONE||tx->SDPtr0||tx->SDPtr1||tx->SDLen0||tx->SDLen1)
     return NDIS_STATUS_FAILURE;
   }else{
    rx=(RXD_STRUC *)cell->AllocVa;
    if(!cell->pNdisPacket||!cell->DmaBuf.AllocVa||cell->DmaBuf.AllocSize!=RX_BUFFER_AGGRESIZE||
       RTMP_GetPhysicalAddressHigh(cell->DmaBuf.AllocPa)||
       le2cpu32(rx->SDP0)!=RTMP_GetPhysicalAddressLow(cell->DmaBuf.AllocPa)||
       rx->DDONE||rx->SDL0!=RX_BUFFER_AGGRESIZE||rx->SDL1||rx->LS0||rx->LS1)
     return NDIS_STATUS_FAILURE;
   }
  }
  rings[i].base=i?MT_RX_RING_BASE+MT_RINGREG_DIFF*(i-1):MT_TX_RING_BASE+MT_RINGREG_DIFF*5;
  rings[i].count=rings[i].base+4;rings[i].cpu=rings[i].base+8;rings[i].dma=rings[i].base+12;
  rings[i].pa=RTMP_GetPhysicalAddressLow(buf->AllocPa);rings[i].size=size;rings[i].cidx=i?size-1:0;
 }
#ifdef RT_BIG_ENDIAN
 return NDIS_STATUS_FAILURE;
#endif
 if(!wr_iot_mcu_boot_pse_empty(ad))return NDIS_STATUS_FAILURE;
 wmb();RTMP_IO_WRITE32(ad,WPDMA_RST_PTR,reset.word);
 for(i=0;i<3;i++){
  RTMP_IO_WRITE32(ad,rings[i].base,rings[i].pa);
  RTMP_IO_WRITE32(ad,rings[i].count,rings[i].size);
  RTMP_IO_WRITE32(ad,rings[i].cpu,rings[i].cidx);
 }
 /* All three readbacks must pass before publishing software indices. */
 for(i=0;i<3;i++){
  RTMP_IO_READ32(ad,rings[i].base,&value);if(value!=rings[i].pa)return NDIS_STATUS_FAILURE;
  RTMP_IO_READ32(ad,rings[i].count,&value);if(value!=rings[i].size)return NDIS_STATUS_FAILURE;
  RTMP_IO_READ32(ad,rings[i].cpu,&value);if(value!=rings[i].cidx)return NDIS_STATUS_FAILURE;
  RTMP_IO_READ32(ad,rings[i].dma,&value);if(value)return NDIS_STATUS_FAILURE;
 }
 if(!wr_iot_mcu_boot_pse_empty(ad))return NDIS_STATUS_FAILURE;
 ad->CtrlRing.hw_desc_base=rings[0].base;ad->CtrlRing.hw_cnt_addr=rings[0].count;
 ad->CtrlRing.hw_cidx_addr=rings[0].cpu;ad->CtrlRing.hw_didx_addr=rings[0].dma;
 ad->CtrlRing.TxSwFreeIdx=ad->CtrlRing.TxCpuIdx=ad->CtrlRing.TxDmaIdx=0;
 for(i=0;i<2;i++){
  ad->RxRing[i].hw_desc_base=rings[i+1].base;ad->RxRing[i].hw_cnt_addr=rings[i+1].count;
  ad->RxRing[i].hw_cidx_addr=rings[i+1].cpu;ad->RxRing[i].hw_didx_addr=rings[i+1].dma;
  ad->RxRing[i].RxSwReadIdx=ad->RxRing[i].RxDmaIdx=0;ad->RxRing[i].RxCpuIdx=RX_RING_SIZE-1;
 }
 return NDIS_STATUS_SUCCESS;
}
