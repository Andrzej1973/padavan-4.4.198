/* Read-only precondition before enabling shared TX DMA. Data remains fenced.
 * Empty packet pointers alone do not prove that no hardware work is pending. */
INT wr_iot_mcu_boot_other_tx_idle(RTMP_ADAPTER *ad)
{
 struct wr_tx_view {RTMP_DMACB *cells;RTMP_DMABUF *storage;UINT32 free,cpu,base,cnt,cidx,didx,size,offset;} v[7];
 UINT32 value;ULONG flags=0;unsigned int i,j;int joined;
 if(!ad||in_atomic()||irqs_disabled()||NUM_OF_TX_RING!=4||TXD_SIZE<sizeof(TXD_STRUC)||
    !wr_iot_mcu_boot_frozen_owned(ad))return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&ad->wr_iot_nettask_lock,flags);
 joined=ad->wr_iot_nettask_data_joined&&!ad->wr_iot_nettask_data_joining&&
        wr_iot_tasklet_schedule_may_join(&ad->wr_iot_nettask_data_owner);
 RTMP_INT_UNLOCK(&ad->wr_iot_nettask_lock,flags);
 if(!joined)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,MT_INT_MASK_CSR,&value);if(value)return NDIS_STATUS_FAILURE;
 RTMP_IO_READ32(ad,MT_WPDMA_GLO_CFG,&value);
 if(value==~(UINT32)0||(value&(TX_DMA_EN|RX_DMA_EN|TX_DMA_BUSY|RX_DMA_BUSY)))return NDIS_STATUS_FAILURE;
#define WR_BOOT_TX_VIEW(n,r,s,count,off) do{v[n].cells=(r).Cell;v[n].storage=&(s);v[n].free=(r).TxSwFreeIdx;v[n].cpu=(r).TxCpuIdx;v[n].base=(r).hw_desc_base;v[n].cnt=(r).hw_cnt_addr;v[n].cidx=(r).hw_cidx_addr;v[n].didx=(r).hw_didx_addr;v[n].size=(count);v[n].offset=(off);}while(0)
 for(i=0;i<4;i++){
  unsigned int offset=i==QID_AC_BE?0x10:i==QID_AC_BK?0:i*0x10;
  WR_BOOT_TX_VIEW(i,ad->TxRing[i],ad->TxDescRing[i],TX_RING_SIZE,offset);
 }
 WR_BOOT_TX_VIEW(4,ad->MgmtRing,ad->MgmtDescRing,MGMT_RING_SIZE,4*MT_RINGREG_DIFF);
 WR_BOOT_TX_VIEW(5,ad->TxBmcRing,ad->TxBmcDescRing,TX_RING_SIZE,QID_BMC*MT_RINGREG_DIFF);
 WR_BOOT_TX_VIEW(6,ad->BcnRing,ad->BcnDescRing,BCN_RING_SIZE,MT_TX_RING_BCN_IDX*MT_RINGREG_DIFF);
#undef WR_BOOT_TX_VIEW
 for(i=0;i<7;i++){
  RTMP_DMABUF *s=v[i].storage;
  if(!s->AllocVa||((ULONG)s->AllocVa&(sizeof(UINT32)-1))||s->AllocSize<v[i].size*TXD_SIZE||
     RTMP_GetPhysicalAddressHigh(s->AllocPa)||(RTMP_GetPhysicalAddressLow(s->AllocPa)&15U)||
     v[i].cpu>=v[i].size||v[i].free!=v[i].cpu||
     v[i].base!=MT_TX_RING_BASE+v[i].offset||v[i].cnt!=v[i].base+4||
     v[i].cidx!=v[i].base+8||v[i].didx!=v[i].base+12)return NDIS_STATUS_FAILURE;
  for(j=0;j<v[i].size;j++){
   RTMP_DMACB *c=&v[i].cells[j];TXD_STRUC *tx=(TXD_STRUC *)c->AllocVa;
   if(c->AllocVa!=(UCHAR *)s->AllocVa+j*TXD_SIZE||c->AllocSize!=TXD_SIZE||
      RTMP_GetPhysicalAddressHigh(c->AllocPa)||
      RTMP_GetPhysicalAddressLow(c->AllocPa)!=RTMP_GetPhysicalAddressLow(s->AllocPa)+j*TXD_SIZE||
      c->pNdisPacket||c->pNextNdisPacket||!tx->DMADONE)return NDIS_STATUS_FAILURE;
  }
  RTMP_IO_READ32(ad,v[i].base,&value);if(value!=RTMP_GetPhysicalAddressLow(s->AllocPa))return NDIS_STATUS_FAILURE;
  RTMP_IO_READ32(ad,v[i].cnt,&value);if(value!=v[i].size)return NDIS_STATUS_FAILURE;
  RTMP_IO_READ32(ad,v[i].cidx,&value);if(value!=v[i].cpu)return NDIS_STATUS_FAILURE;
  RTMP_IO_READ32(ad,v[i].didx,&value);if(value!=v[i].cpu)return NDIS_STATUS_FAILURE;
 }
#ifdef RT_BIG_ENDIAN
 return NDIS_STATUS_FAILURE;
#endif
 return wr_iot_mcu_boot_frozen_owned(ad)?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
