/* Sole frozen owner after ROM quiesce. Refresh payload storage only; indices,
 * hardware base/count and sequence ledger remain unchanged until ring rearm. */
INT wr_iot_mcu_boot_rx_refresh(RTMP_ADAPTER *ad)
{
 struct wr_rx_replacement {PNDIS_PACKET packet;RTMP_DMABUF buffer;};
 struct wr_rx_replacement *fresh=NULL;
 unsigned int ring,index,count=0,empty=0,i,word;INT status=NDIS_STATUS_FAILURE;
 POS_COOKIE cookie;RTMP_DMACB *cell;
 union {RXD_STRUC descriptor;UINT32 word[RXD_SIZE/sizeof(UINT32)];} desc;
 if(!ad||in_atomic()||irqs_disabled()||NUM_OF_RX_RING!=2||
    RXD_SIZE<sizeof(RXD_STRUC)||RX_BUFFER_AGGRESIZE>0x3fffU||
    !wr_iot_mcu_boot_pse_empty(ad))return NDIS_STATUS_FAILURE;
 cookie=(POS_COOKIE)ad->OS_Cookie;
 if(!cookie||!cookie->pci_dev)return NDIS_STATUS_FAILURE;
 if(wr_iot_mcu_boot_rx_discard_batch(ad,&empty)!=NDIS_STATUS_SUCCESS||!empty)
  return NDIS_STATUS_FAILURE;
 if(os_alloc_mem(ad,(UCHAR **)&fresh,2*RX_RING_SIZE*sizeof(*fresh))!=NDIS_STATUS_SUCCESS||!fresh)
  return NDIS_STATUS_FAILURE;
 NdisZeroMemory(fresh,2*RX_RING_SIZE*sizeof(*fresh));
 for(i=0;i<2*RX_RING_SIZE;i++){
  fresh[i].buffer.AllocSize=RX_BUFFER_AGGRESIZE;
  fresh[i].packet=RTMP_AllocateRxPacketBuffer(ad,cookie->pci_dev,
    RX_BUFFER_AGGRESIZE,FALSE,&fresh[i].buffer.AllocVa,&fresh[i].buffer.AllocPa);
  if(!fresh[i].packet)goto out;
  /* A failed DMA mapping is not owned and must not be unmapped. */
  if(DMA_MAPPING_ERROR(cookie->pci_dev,fresh[i].buffer.AllocPa)){
   RELEASE_NDIS_PACKET(ad,fresh[i].packet,NDIS_STATUS_FAILURE);
   fresh[i].packet=NULL;goto out;
  }
  count++;
  if(!fresh[i].buffer.AllocVa||RTMP_GetPhysicalAddressHigh(fresh[i].buffer.AllocPa))goto out;
 }
 /* Allocations may sleep: revalidate before the irreversible ownership swap. */
 if(!wr_iot_mcu_boot_pse_empty(ad))goto out;
 for(ring=0;ring<2;ring++)for(index=0;index<RX_RING_SIZE;index++){
  struct wr_rx_replacement old;
  i=ring*RX_RING_SIZE+index;cell=&ad->RxRing[ring].Cell[index];
  old.packet=cell->pNdisPacket;old.buffer=cell->DmaBuf;
  cell->pNdisPacket=fresh[i].packet;cell->DmaBuf=fresh[i].buffer;
  fresh[i]=old;
  NdisZeroMemory(&desc,sizeof(desc));
  desc.descriptor.SDP0=RTMP_GetPhysicalAddressLow(cell->DmaBuf.AllocPa);
  desc.descriptor.SDL0=RX_BUFFER_AGGRESIZE;
  /* Coherent descriptors, DMA disabled; publish every word before any rearm. */
  for(word=0;word<RXD_SIZE/sizeof(UINT32);word++)desc.word[word]=cpu2le32(desc.word[word]);
  NdisMoveMemory(cell->AllocVa,&desc,RXD_SIZE);
 }
 wmb();
 status=wr_iot_mcu_boot_pse_empty(ad)?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
out:
 /* Before commit: new mappings. After commit: old mappings. Exactly one owner. */
 for(i=0;i<count;i++){
  PCI_UNMAP_SINGLE(ad,fresh[i].buffer.AllocPa,fresh[i].buffer.AllocSize,RTMP_PCI_DMA_FROMDEVICE);
  RELEASE_NDIS_PACKET(ad,fresh[i].packet,NDIS_STATUS_SUCCESS);
 }
 os_free_mem(ad,fresh);
 return status;
}
