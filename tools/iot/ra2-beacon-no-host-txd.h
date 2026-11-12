/* Unbound descriptor format check only. This never establishes live skb,
 * producer, DMA/ring ownership, cold epoch or permission to submit. Caller
 * must pin the actual packet and bound its readable data before this copy. */
#ifndef WR_IOT_RA2_BEACON_NO_HOST_TXD_H
#define WR_IOT_RA2_BEACON_NO_HOST_TXD_H
static inline int wr_iot_ra2_no_host_txd(const void *bytes,unsigned int length)
{
#ifdef RT_BIG_ENDIAN
 (void)bytes;(void)length;return 0;
#else
 TMAC_TXD_L descriptor;
 if(!bytes||length<sizeof(descriptor))return 0;
 NdisMoveMemory(&descriptor,bytes,sizeof(descriptor));
 return descriptor.txd_0.p_idx==P_IDX_LMAC&&
  descriptor.txd_0.q_idx==Q_IDX_BCN&&
  descriptor.txd_1.ft==TMI_FT_LONG&&descriptor.txd_1.own_mac==0x12&&
  descriptor.txd_1.wlan_idx==0&&descriptor.txd_1.no_ack==1&&
  descriptor.txd_1.hdr_format==TMI_HDR_FT_NOR_80211&&
  descriptor.txd_2.frm_type==FC_TYPE_MGMT&&
  descriptor.txd_2.sub_type==SUBTYPE_BEACON&&descriptor.txd_2.bc_mc_pkt&&
  !descriptor.txd_5.tx_status_2_host&&!descriptor.txd_5.tx_status_2_mcu&&
  !descriptor.txd_5.pid;
#endif
}
#endif
