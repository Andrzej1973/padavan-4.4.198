#include <assert.h>
#include <stdio.h>
typedef unsigned UINT32;
typedef struct {unsigned mac,reg,writes,reads,fault;} RTMP_ADAPTER;
#define ARB_SCR 1
#define MT_ARB_SCR_TXDIS 1
#define MT_ARB_SCR_RXDIS 2
/* Cross-check the operation's complete field mask with the actual SDK. */
#include "mac/mac_mt/wf_tmac.h"
static unsigned read_reg(RTMP_ADAPTER *a,unsigned reg)
{
 a->reads++;
 if(reg==ARB_SCR)return a->fault==3&&a->writes?0:a->mac;
 assert(reg==TMAC_ICR);
 return a->fault==2&&a->writes?a->reg^1:a->reg;
}
static void write_reg(RTMP_ADAPTER *a,unsigned reg,unsigned value)
{assert(reg==TMAC_ICR);a->writes++;if(a->fault!=1)a->reg=value;}
#define RTMP_IO_READ32(a,r,p) (*(p)=read_reg(a,r))
#define RTMP_IO_WRITE32(a,r,v) write_reg(a,r,v)
#include "mcu-config-slot-mmio.inc"
int main(void)
{
 assert((ICR_EIFS_TIME_MASK|ICR_RIFS_TIME_MASK|ICR_SIFS_TIME_MASK|
         ICR_SLOT_TIME_MASK)==0x7f7f7dffU);
 for(unsigned fault=0;fault<4;fault++){
  RTMP_ADAPTER ad={.mac=3,.reg=0x80808200,.fault=fault};
  assert(wr_iot_config_slot_mmio(&ad,0x090a0854)==!fault);
  assert(ad.writes==1&&ad.mac==3);
  if(!fault)assert(ad.reg==0x898a8a54);
 }
 for(unsigned mac=0;mac<4;mac++)if(mac!=3){
  RTMP_ADAPTER ad={.mac=mac};assert(!wr_iot_config_slot_mmio(&ad,0)&&!ad.writes);
 }
 RTMP_ADAPTER ad={.mac=~0U};assert(!wr_iot_config_slot_mmio(&ad,0)&&!ad.writes);
 ad=(RTMP_ADAPTER){.mac=3,.reg=~0U};assert(!wr_iot_config_slot_mmio(&ad,0)&&!ad.writes);
 ad=(RTMP_ADAPTER){.mac=3};assert(!wr_iot_config_slot_mmio(&ad,0x80000000)&&!ad.reads);
 assert(!wr_iot_config_slot_mmio(NULL,0));
 puts("PASS isolated slot MMIO: disabled MAC, reserved-bit preservation, readback mismatch, dropped write, MAC drift and absent-device refusal; owner/firmware exclusion not provided");
}
