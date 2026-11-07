/* Sole frozen ROM owner after callback/controller joins and DMA stop.
 * Retire packet mappings, not sequence IDs. Hardware indices remain untouched. */
INT wr_iot_mcu_boot_control_retire(RTMP_ADAPTER *ad)
{
 unsigned int i,j;ULONG flags=0;INT status=NDIS_STATUS_FAILURE;
 RTMP_DMACB *cell;RTMP_CTRL_RING *ring;TXD_STRUC *tx;
 PACKET_INFO info;UCHAR *data;UINT length;
#ifdef RT_BIG_ENDIAN
 /* This board's little-endian ABI is the only reviewed control descriptor path. */
 return NDIS_STATUS_FAILURE;
#endif
 if(!ad||in_atomic()||irqs_disabled()||TXD_SIZE<sizeof(TXD_STRUC)||
    !wr_iot_mcu_boot_pse_empty(ad))return NDIS_STATUS_FAILURE;
 ring=&ad->CtrlRing;
 RTMP_SPIN_LOCK_IRQSAVE(&ad->CtrlRingLock,&flags);
 if(!ad->CtrlDescRing.AllocVa||ad->CtrlDescRing.AllocSize<MGMT_RING_SIZE*TXD_SIZE||
    ring->TxSwFreeIdx>=MGMT_RING_SIZE||ring->TxCpuIdx>=MGMT_RING_SIZE||
    ring->TxDmaIdx>=MGMT_RING_SIZE)goto out;
 /* Validate every cell before releasing anything; never infer ownership from
  * DMA index alone. Completed descriptors can still hold owned packets. */
 for(i=0;i<MGMT_RING_SIZE;i++){
  cell=&ring->Cell[i];
  if(cell->AllocVa!=(UCHAR *)ad->CtrlDescRing.AllocVa+i*TXD_SIZE||
     ((ULONG)cell->AllocVa&(sizeof(UINT32)-1))||cell->AllocSize!=TXD_SIZE||
     cell->pNextNdisPacket)goto out;
  if(!cell->pNdisPacket)continue;
  tx=(TXD_STRUC *)cell->AllocVa;
  if(RTMP_GetPhysicalAddressHigh(cell->PacketPa)||
     tx->SDPtr0!=RTMP_GetPhysicalAddressLow(cell->PacketPa)||
     !tx->SDLen0||tx->SDLen1||!tx->LastSec0||tx->LastSec1)goto out;
  RTMP_QueryPacketInfo(cell->pNdisPacket,&info,&data,&length);
  if(!data||length!=tx->SDLen0)goto out;
  for(j=0;j<i;j++)if(ring->Cell[j].pNdisPacket&&
    (ring->Cell[j].pNdisPacket==cell->pNdisPacket||
     ring->Cell[j].PacketPa==cell->PacketPa))goto out;
 }
 for(i=0;i<MGMT_RING_SIZE;i++){
  cell=&ring->Cell[i];tx=(TXD_STRUC *)cell->AllocVa;
  if(cell->pNdisPacket){
   PNDIS_PACKET packet=cell->pNdisPacket;
   cell->pNdisPacket=NULL;
   PCI_UNMAP_SINGLE(ad,cell->PacketPa,tx->SDLen0,RTMP_PCI_DMA_TODEVICE);
   RELEASE_NDIS_PACKET(ad,packet,NDIS_STATUS_SUCCESS);
  }
  cell->PacketPa=0;
  NdisZeroMemory(cell->AllocVa,TXD_SIZE);tx->DMADONE=1;
 }
 wmb();status=NDIS_STATUS_SUCCESS;
out:
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->CtrlRingLock,&flags);
 if(status==NDIS_STATUS_SUCCESS&&!wr_iot_mcu_boot_pse_empty(ad))status=NDIS_STATUS_FAILURE;
 return status;
}
