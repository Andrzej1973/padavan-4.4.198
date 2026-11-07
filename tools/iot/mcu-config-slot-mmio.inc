/* Low-level operation for the isolated generated candidate.
 * Caller must hold an exclusive config lifetime/transition lease and prove
 * no previously submitted firmware timing writer can still execute.
 * Does not enable MAC, retire journal entries, or grant config completion. */
static int wr_iot_config_slot_mmio(RTMP_ADAPTER *ad,unsigned int expected)
{
 UINT32 before,after,mac;
 const UINT32 mask=0x7f7f7dffU;
 if(!ad||(expected&~mask))return 0;
 RTMP_IO_READ32(ad,ARB_SCR,&mac);
 if(mac==~(UINT32)0||(mac&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
    (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))return 0;
 RTMP_IO_READ32(ad,TMAC_ICR,&before);
 if(before==~(UINT32)0)return 0;
 RTMP_IO_WRITE32(ad,TMAC_ICR,(before&~mask)|expected);
 RTMP_IO_READ32(ad,TMAC_ICR,&after);
 if(after!=((before&~mask)|expected))return 0;
 RTMP_IO_READ32(ad,ARB_SCR,&mac);
 return mac!=~(UINT32)0&&
  (mac&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))==(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS);
}
