#ifndef WR_IOT_CONTROL_RECORD_COMMON_H
#define WR_IOT_CONTROL_RECORD_COMMON_H
#include <stdio.h>
#include "saved-config.h"
#define WR_IOT_CONTROL_RECORD_MAX 512
static inline int wr_iot_control_id(const char *id){
 size_t index;if(!id||strlen(id)!=32)return 0;
 for(index=0;index<32;index++)if(!((id[index]>='0'&&id[index]<='9')||
    (id[index]>='a'&&id[index]<='f')))return 0;
 return 1;
}
static inline int wr_iot_control_time(const char *text,unsigned long long *out){
 unsigned long long number=0,digit;const unsigned long long limit=~0ULL;
 if(!text||!*text||*text=='0')return 0;
 for(;*text;text++){
  if(*text<'0'||*text>'9')return 0;
  digit=(unsigned)(*text-'0');if(number>(limit-digit)/10)return 0;number=number*10+digit;
 }
 *out=number;return 1;
}
#endif
