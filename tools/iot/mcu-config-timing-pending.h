/* Exact no-response request journal; caller holds owner/transition locks.
 * No hardware observation or proof retirement is supplied here. */
#ifndef WR_IOT_CONFIG_TIMING_PENDING_H
#define WR_IOT_CONFIG_TIMING_PENDING_H
#include "mcu-config-rf-pending.h"
struct wr_iot_config_timing_pending {
 struct wr_iot_config_rf_pending ticket;
 unsigned char bytes[36];
};
static inline int wr_iot_config_timing_valid(unsigned int ext,
 const unsigned char *data,unsigned int length)
{
 unsigned int i,seen=0;
 if(!data)return 0;
 if(ext==0x28U)return length==8&&!data[3]&&!data[6]&&!data[7];
 if(ext!=0x27U||length<4||!data[0]||data[0]>4||length!=4U+8U*data[0]||
    data[1]||data[2]||data[3])return 0;
 for(i=0;i<data[0];i++){
  const unsigned char *p=data+4+8*i;
  if(p[0]>3||!p[1]||(p[1]&~15U)||(seen&(1U<<p[0]))||
     ((p[1]&1U)&&p[2]>15))return 0;
  seen|=1U<<p[0];
 }
 return 1;
}
static inline int wr_iot_config_timing_record(struct wr_iot_config_timing_pending *p,
 unsigned long peer,unsigned long radio,unsigned long epoch,unsigned long close,
 unsigned long close_epoch,unsigned int ext,const unsigned char *data,unsigned int length)
{
 unsigned int i;
 if(!p||!wr_iot_config_timing_valid(ext,data,length)||
    !wr_iot_config_rf_record(&p->ticket,peer,radio,epoch,close,close_epoch,ext,length,0))return 0;
 for(i=0;i<length;i++)p->bytes[i]=data[i];
 return 1;
}
#endif
