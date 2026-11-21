#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "mac/mac_mt/wf_tmac.h"
#define BIT8 (1U<<8)
#define BIT9 (1U<<9)
#include "mac/mac_mt/wf_arb.h"
#include "mcu-config-edca-plan.h"
typedef unsigned UINT32;
typedef struct {unsigned mac,reg[6],writes,fail_at,drop,drift;} RTMP_ADAPTER;
static const unsigned register_addresses[6]={TMAC_ACTXOPLR1,TMAC_ACTXOPLR0,
 ARB_AIFSR0,ARB_ACCWIR0,ARB_ACCWXR0,ARB_ACCWXR1};
static unsigned read_reg(RTMP_ADAPTER *a,unsigned address)
{
 if(address==ARB_SCR)return a->drift&&a->writes?0:a->mac;
 for(unsigned i=0;i<6;i++)if(register_addresses[i]==address)return a->reg[i];
 assert(0);return 0;
}
static void write_reg(RTMP_ADAPTER *a,unsigned address,unsigned value)
{
 a->writes++;
 for(unsigned i=0;i<6;i++)if(register_addresses[i]==address){
  if(a->writes==a->fail_at){if(!a->drop)a->reg[i]=value^1;}
  else a->reg[i]=value;
  return;
 }
 assert(0);
}
#define RTMP_IO_READ32(a,r,p) (*(p)=read_reg(a,r))
#define RTMP_IO_WRITE32(a,r,v) write_reg(a,r,v)
#include "mcu-config-edca-mmio.inc"
int main(void)
{
 const unsigned addresses[4][4]={
  {ARB_AIFSR0,ARB_ACCWIR0,ARB_ACCWXR0,TMAC_ACTXOPLR1},
  {ARB_AIFSR0,ARB_ACCWIR0,ARB_ACCWXR0,TMAC_ACTXOPLR1},
  {ARB_AIFSR0,ARB_ACCWIR0,ARB_ACCWXR1,TMAC_ACTXOPLR0},
  {ARB_AIFSR0,ARB_ACCWIR0,ARB_ACCWXR1,TMAC_ACTXOPLR0}};
 for(unsigned ac=0;ac<4;ac++)for(unsigned bit=0;bit<4;bit++){
  unsigned char request[12]={1,0,0,0,ac,1U<<bit,7,0xa5,0x34,0x12,0xcd,0xab};
  struct wr_iot_edca_plan plan;
  unsigned shifts[4]={ac*4,ac*8,(ac%2)*16,(ac%2)*16};
  unsigned masks[4]={15,255,65535,65535};
  unsigned values[4]={7,0xa5,0x1234,0xabcd};
  assert(wr_iot_config_edca_plan(request,sizeof(request),&plan));
  unsigned found=0;
  for(unsigned i=0;i<6;i++)if(plan.mask[i]){
   found++;assert(plan.address[i]==addresses[ac][bit]);
   assert(plan.mask[i]==(masks[bit]<<shifts[bit]));
   assert(plan.value[i]==(values[bit]<<shifts[bit]));
  }
  assert(found==1);
 }
 unsigned char all[36]={4};
 for(unsigned ac=0;ac<4;ac++){
  unsigned char *p=all+4+8*ac;p[0]=ac;p[1]=15;p[2]=ac+1;p[3]=ac+2;
  p[4]=ac+3;p[5]=1;p[6]=ac+4;p[7]=2;
 }
 struct wr_iot_edca_plan plan,before;
 assert(wr_iot_config_edca_plan(all,36,&plan));
 assert(plan.mask[0]==~0U&&plan.mask[1]==~0U&&plan.mask[2]==65535U&&
        plan.mask[3]==~0U&&plan.mask[4]==~0U&&plan.mask[5]==~0U);
 before=plan;all[12]=0;
 assert(!wr_iot_config_edca_plan(all,36,&plan)&&!memcmp(&plan,&before,sizeof(plan)));
 all[12]=1;all[6]=16;
 assert(!wr_iot_config_edca_plan(all,36,&plan)&&!memcmp(&plan,&before,sizeof(plan)));
 assert(!wr_iot_config_edca_plan(NULL,36,&plan));
 assert(!wr_iot_config_edca_plan(all,36,NULL));
 all[6]=1;
 for(unsigned fault=0;fault<15;fault++){
  RTMP_ADAPTER ad={.mac=MT_ARB_SCR_TXDIS|MT_ARB_SCR_RXDIS};
  for(unsigned i=0;i<6;i++)ad.reg[i]=0x80808080;
  if(fault>=1&&fault<=6)ad.fail_at=fault;
  if(fault>=7&&fault<=12){ad.fail_at=fault-6;ad.drop=1;}
  if(fault==13)ad.drift=1;
  if(fault==14)ad.reg[5]=~0U;
  assert(wr_iot_config_edca_mmio(&ad,all,36)==!fault);
  assert(ad.writes==(fault==14?0:fault==13?1:fault?ad.fail_at:6));
  if(!fault){
   assert(wr_iot_config_edca_plan(all,36,&plan));
   for(unsigned i=0;i<6;i++)assert(ad.reg[i]==((0x80808080&~plan.mask[i])|plan.value[i]));
  }
 }
 puts("PASS EDCA MMIO: all six writes/readbacks, every partial-write failure, MAC drift, snapshot failure before writes and bit preservation; owner/firmware exclusion remains external");
 puts("PASS EDCA plan: four queues, every valid bit, SDK addresses, LE fields, merged masks and invalid output preservation; no hardware proof");
}
