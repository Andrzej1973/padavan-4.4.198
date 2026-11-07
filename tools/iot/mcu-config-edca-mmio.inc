/* Caller holds exclusive config/lifetime lease and excludes firmware writers.
 * Partial failure is retained by owner; no rollback or data admission grant. */
static int wr_iot_config_edca_mmio(RTMP_ADAPTER *ad,const unsigned char *data,
 unsigned int length)
{
 struct wr_iot_edca_plan plan;UINT32 saved[6],value,mac;unsigned int i;
 if(!ad||!wr_iot_config_edca_plan(data,length,&plan))return 0;
 RTMP_IO_READ32(ad,ARB_SCR,&mac);
 if(mac==~(UINT32)0||(mac&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
    (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))return 0;
 for(i=0;i<6;i++)if(plan.mask[i]){
  RTMP_IO_READ32(ad,plan.address[i],&saved[i]);
  if(saved[i]==~(UINT32)0)return 0;
 }
 for(i=0;i<6;i++)if(plan.mask[i]){
  RTMP_IO_READ32(ad,ARB_SCR,&mac);
  if(mac==~(UINT32)0||(mac&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))!=
     (MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))return 0;
  value=(saved[i]&~plan.mask[i])|plan.value[i];
  RTMP_IO_WRITE32(ad,plan.address[i],value);
  RTMP_IO_READ32(ad,plan.address[i],&mac);
  if(mac!=value)return 0;
 }
 RTMP_IO_READ32(ad,ARB_SCR,&mac);
 return mac!=~(UINT32)0&&
  (mac&(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS))==(MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS);
}
