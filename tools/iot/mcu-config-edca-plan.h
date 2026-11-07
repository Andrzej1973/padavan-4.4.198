/* SDK WMM register plan only. No I/O or completion/admission grant.
 * Requires wf_tmac.h/wf_arb.h register definitions and timing validator. */
#ifndef WR_IOT_CONFIG_EDCA_PLAN_H
#define WR_IOT_CONFIG_EDCA_PLAN_H
#include "mcu-config-timing-pending.h"
struct wr_iot_edca_plan {
 unsigned int address[6],mask[6],value[6];
};
static inline int wr_iot_config_edca_plan(const unsigned char *data,
 unsigned int length,struct wr_iot_edca_plan *out)
{
 struct wr_iot_edca_plan plan={
  {TMAC_ACTXOPLR1,TMAC_ACTXOPLR0,ARB_AIFSR0,ARB_ACCWIR0,ARB_ACCWXR0,ARB_ACCWXR1},
  {0,0,0,0,0,0},{0,0,0,0,0,0}};
 unsigned int i;
 if(!out||!wr_iot_config_timing_valid(0x27,data,length))return 0;
 for(i=0;i<data[0];i++){
  const unsigned char *p=data+4+8*i;
  unsigned int ac=p[0],valid=p[1],shift,index,value;
  if(valid&1U){
   shift=4U*ac;plan.mask[2]|=15U<<shift;plan.value[2]|=(unsigned int)p[2]<<shift;
  }
  if(valid&2U){
   shift=8U*ac;plan.mask[3]|=255U<<shift;plan.value[3]|=(unsigned int)p[3]<<shift;
  }
  if(valid&4U){
   index=4U+ac/2U;shift=16U*(ac%2U);
   value=(unsigned int)p[4]|((unsigned int)p[5]<<8);
   plan.mask[index]|=65535U<<shift;plan.value[index]|=value<<shift;
  }
  if(valid&8U){
   index=ac/2U;shift=16U*(ac%2U);
   value=(unsigned int)p[6]|((unsigned int)p[7]<<8);
   plan.mask[index]|=65535U<<shift;plan.value[index]|=value<<shift;
  }
 }
 *out=plan;
 return 1;
}
#endif
